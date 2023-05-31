from datetime import date
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta


class EmployeeSeparation(models.Model):
    _name = "hr.employee.separation"
    _description = "Employee Separation Request"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def button_confirm(self):
        for rec in self:

            # Make request date to today's date
            rec.date_of_request = fields.Date.today()

            # Trigger mail to reporting manager to approve this
            rec.send_notification_mail_to_manager()

            # Change employee state to "Notice Period"
            rec.employee_id.state = "notice_period"

            rec.state = "confirm"

    def button_confirm_manager(self):
        for rec in self:
            rec.state = "validated"

            # Check for user privilege
            current_user = self.env.user
            if not (self.user_has_groups('hr.group_hr_manager') or
                    rec.employee_id.parent_id.user_id == current_user
                    or current_user == rec.hr_responsible_id):
                raise ValidationError(_("You are not allowed to do this. Only HR Manager or %s or %s can do this")%(rec.hr_responsible_id.name, rec.employee_id.parent_id.name))

            # Send notification mail to hr manager after getting approval from line manager
            rec.send_notification_mail_to_manager(act_type="approve")

    def button_confirm_hr(self):
        for rec in self:

            # Check for user privilege
            if not rec.last_working_date_approved:
                raise ValidationError(_("Please fill the last working date for this employee"))

            current_user = self.env.user
            if not (self.user_has_groups('hr.group_hr_manager')
                    or current_user == rec.hr_responsible_id):
                raise ValidationError(_("You are not allowed to do this. Only HR Manager or %s can do this") %
                                      (rec.hr_responsible_id.name))

            rec.state = "approved"

    def button_completed(self):
        for rec in self:
            for checklist in rec.checklist_ids:
                if not checklist.completed:
                    raise ValidationError(_("Please complete the checklist and try again"))

            if rec.last_working_date_approved:
                if rec.last_working_date_approved > fields.Date.today():
                    raise ValidationError(_("Approved last working day is %s. You cannot do this now.")%(rec.last_working_date_approved.strftime("%d %B, %Y")))
            else:
                raise ValidationError(_("Please fill the last working date for this employee"))

            # Change employee state to "Resigned"
            rec.employee_id.state = "resigned"

            # Create payslip input request to pull this amount on the payslip
            rec.create_payslip_input_request()

            rec.state = "completed"

    def create_payslip_input_request(self):
        for rec in self:
            if rec.settlement_amount:
                input_category_id = self.env['hr.employee.extra.input.category'].search([('code','=','INDEMNITY')])
                data = {
                    "employee_id": rec.employee_id.id,
                    "input_category_id": input_category_id[0].id,
                    "note": rec.calculations,
                    "date": rec.last_working_day,
                    "amount": rec.settlement_amount,
                    "input_line_ids": [
                        (
                            0, 0,
                            {'effective_date': rec.last_working_day, 'amount': rec.settlement_amount}
                        )
                    ]
                }
                request_id = self.env['hr.employee.input.requests'].create(data)
                request_id.action_validate()
                request_id.action_approve()


    def button_back_off(self):
        for rec in self:

            # Change employee state to "Employment"
            rec.employee_id.state = "employment"

            rec.state = "back_off"

    def fetch_checklist(self):
        for rec in self:
            checklist_ids = self.env['hr.employee.checklist'].search(
                [
                    ("type", "=", rec.type),
                ],
                order='sequence asc'
            )
            vals = []
            if checklist_ids:
                for check in checklist_ids:
                    vals.append((0, 0, {
                        "checklist_id": check.id
                    }))
            rec.checklist_ids = vals

    @api.model
    def _default_employee_id(self):
        employee = self.env.user.employee_id
        if not employee:
            raise ValidationError(_('The current user has no related employee. Please, create one.'))
        return employee

    @api.depends('notice_period')
    def _compute_last_working_day(self):
        for rec in self:
            rec.last_working_day = fields.Date.today() + timedelta(days=int(rec.notice_period or 0))

    @api.depends("last_working_date_approved", "employee_id")
    def _compute_end_of_service_benefits(self):
        for rec in self:
            if rec.employee_id and rec.employee_id.contract_id and rec.last_working_date_approved:
                total_years = rec.employee_id.contract_id._get_total_years_of_service(rec.last_working_date_approved)
                basic_pay = rec.employee_id.contract_id.wage
                pay_percentage = 0
                total_indemnity = 0
                calculations = ''

                tmp_total_years = total_years
                if rec.checklist_type_id:
                    months = 0.0
                    for chk_conf in rec.checklist_type_id.settlement_conf_ids:
                        if chk_conf.to_year <= tmp_total_years:

                            days = chk_conf.days
                            pay_percentage = chk_conf.pay_percentage
                            paid_days = chk_conf.paid_days
                            m = 0.0
                            if paid_days:
                                m = ((float(days) * chk_conf.to_year) / paid_days)
                                months += m
                            tmp_total_years -= chk_conf.to_year
                            calculations += 'Indemnity Band %s to %s ==> %s * %s = %s days. So, %s / %s = %s months \n' % (
                                chk_conf.from_year,
                                chk_conf.to_year,
                                days,
                                chk_conf.to_year,
                                float(days) * chk_conf.to_year,
                                days * chk_conf.to_year,
                                paid_days,
                                m
                            )

                        else:

                            days = chk_conf.days
                            pay_percentage = chk_conf.pay_percentage
                            paid_days = chk_conf.paid_days
                            m = 0.0
                            if paid_days:
                                m = ((float(days) * tmp_total_years) / paid_days)
                                months += m
                            calculations += 'Indemnity Band %s to %s ==> %s * %s = %s days. So, %s / %s = %s months \n' % (
                                chk_conf.from_year,
                                chk_conf.to_year,
                                days,
                                tmp_total_years,
                                float(days) * tmp_total_years,
                                days * tmp_total_years,
                                paid_days,
                                m
                            )
                            tmp_total_years -= tmp_total_years
                            break

                    if pay_percentage:
                        if months > 18:
                            months = 18
                        indemnity_amount = months * basic_pay
                        total_indemnity += ((indemnity_amount * pay_percentage) / 100)
                        calculations += 'Total %s months, Indemnity pay percentage is %s and basic pay is %s\n'\
                                        %(months, pay_percentage, basic_pay)
                        calculations += 'Indemnity Payable is %s percentage of %s * %s is %s \n\n'\
                                        %(total_indemnity, months, basic_pay, total_indemnity)
                        calculations += 'Ref :- https://kuwaitnewz.com/kuwait-indemnity-calculator/'
                rec.settlement_amount = total_indemnity
                rec.total_service_in_years = total_years
                rec.calculations = calculations

    name = fields.Char(string="Name")
    employee_id = fields.Many2one("hr.employee", string="Employee", required=True, tracking=True,
                                  default=lambda self: self._default_employee_id())
    user_id = fields.Many2one('res.users', copy=False, tracking=True, string='User',
                              related="employee_id.user_id", related_sudo=True, compute_sudo=True)
    job_title = fields.Char(related="employee_id.job_title", store=True)
    department_id = fields.Many2one(related="employee_id.department_id", store=True)
    work_email = fields.Char(related="employee_id.work_email", store=True)
    contract_id = fields.Many2one(related="employee_id.contract_id", string="Active Contract", store=True)
    notice_period = fields.Integer(related="employee_id.contract_id.notice_period", store=True)

    manager_id = fields.Many2one(related="employee_id.parent_id", store=True)
    hr_responsible_id = fields.Many2one(related="employee_id.contract_id.hr_responsible_id", store=True)

    date_of_request = fields.Date(string="Requested Date", default=fields.Date.today(),
                                  required=True, tracking=True, help="Date of Resignation")
    last_working_date_requested = fields.Date(string="Expected Re-leaving Date", required=True, tracking=True,
                                              help="Expected date of re-leaving")
    last_working_day = fields.Date(string="Re-leaving Date as per Contract", required=False, tracking=True,
                                   compute='_compute_last_working_day',
                                   help="Actual Re-leaving date as per contract and notice period")
    last_working_date_approved = fields.Date(string="Approved Re-leaving Date", required=False, tracking=True,
                                             help="Re-leaving date approved by management")
    reason = fields.Text(string="Reason for Separation", required=True, tracking=True)
    company_id = fields.Many2one('res.company', required=True, readonly=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one(related="company_id.currency_id", string="Currency", readonly=True, store=True,
                                  compute_sudo=True)
    checklist_type_id = fields.Many2one('hr.employee.checklist.type', string='Separation Type', tracking=True, required=True)
    type = fields.Selection(related="checklist_type_id.type", string="Internal Type", store=True)
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('confirm', 'Confirm'),
            ('validated','Validated By Manager'),
            ('approved', 'Approved By HR'),
            ('completed', 'Completed'),
            ('back_off', 'Back Off'),
            ('reject', 'Rejected')
        ], string="Status", default="draft", required=True, tracking=True)

    checklist_ids = fields.One2many("hr.employee.checklist.separation", "separation_id", tracking=True)

    # Calculations
    total_service_in_years = fields.Float(string="Total Service in Years", compute="_compute_end_of_service_benefits", store=True)
    settlement_amount = fields.Monetary(string="Indemnity Amount",
                                        compute="_compute_end_of_service_benefits", store=True,
                                        currency_field='currency_id')
    calculations = fields.Text(string="Calculations", compute="_compute_end_of_service_benefits", store=True)

    @api.model_create_multi
    def create(self, vals):
        request = super(EmployeeSeparation, self).create(vals)
        if not request.name:
            request.name = self.env[
                'ir.sequence'].next_by_code('jic.employee.resignation.request')
        request.fetch_checklist()
        return request

    def unlink(self):
        for ip in self:
            if ip.state != 'draft':
                raise ValidationError(_("Cannot delete record that not in state 'Draft'"))
        return super(EmployeeSeparation, self).unlink()

    @api.returns('self', lambda value: value.id)
    def copy(self):
        raise UserError(_('You cannot duplicate a separation request.'))


    def send_notification_mail_to_manager(self, act_type='validate'):
        """
        Notification mail to reporting manager
        :param act_type:
        :return:
        """
        template = self.env.ref('jic_hr_employee_entry_exit.email_template_employee_resignation', False)
        partner_to = self.employee_id.parent_id.user_id.partner_id.id
        partner_to_name = self.employee_id.parent_id.user_id.partner_id.name

        if act_type == 'approve':
            partner_to = self.hr_responsible_id.partner_id.id
            partner_to_name = self.hr_responsible_id.partner_id.name
        message_composer = self.env['mail.compose.message'].with_context(
            default_use_template=bool(template),
            force_email=True, mail_notify_author=True,
            partner_to=partner_to,partner_to_name=partner_to_name,act_type=act_type
        ).create({
            'res_id': self.id,
            'template_id': template and template.id or False,
            'model': 'hr.employee.separation',
            'composition_mode': 'comment'})

        # Simulate the onchange (like trigger in form the view)
        update_values = message_composer._onchange_template_id(template.id, 'comment', 'hr.employee.separation', self.id)['value']
        message_composer.write(update_values)
        message_composer._action_send_mail()


class EmployeeChecklistSeparation(models.Model):
    _name = "hr.employee.checklist.separation"

    def button_done(self):
        for rec in self:

            current_user = self.env.user
            if not (self.user_has_groups('hr.group_hr_manager')
                    or current_user == rec.separation_id.hr_responsible_id):
                raise ValidationError(_("You are not allowed to do this. Only HR Manager or %s can do this") %
                                      (rec.separation_id.hr_responsible_id.name))

            rec.write(
                {
                    "done_by": self.env.user.id,
                    "done_date": fields.Date.today(),
                    "completed": True
                }
            )

    def button_reset(self):
        for rec in self:

            current_user = self.env.user
            if not (self.user_has_groups('hr.group_hr_manager')
                    or current_user == rec.separation_id.hr_responsible_id):
                raise ValidationError(_("You are not allowed to do this. Only HR Manager or %s can do this") %
                                      (rec.separation_id.hr_responsible_id.name))

            rec.write(
                {
                    "done_by": False,
                    "done_date": False,
                    "completed": False
                }
            )

    checklist_id = fields.Many2one("hr.employee.checklist", string="Checklist", required=True)
    notes = fields.Text(string="Notes", required=False)
    done_by = fields.Many2one("res.users", "Processed By")
    done_date = fields.Date(string="Processed On")
    completed = fields.Boolean(string="Completed")

    separation_id = fields.Many2one("hr.employee.separation", string="Separation", ondelete='cascade')


class EmployeeChecklistOnBoarding(models.Model):
    _name = "hr.employee.checklist.onboarding"

    def button_done(self):
        for rec in self:

            current_user = self.env.user
            if not (self.user_has_groups('hr.group_hr_manager')
                    or current_user == rec.separation_id.hr_responsible_id):
                raise ValidationError(_("You are not allowed to do this. Only HR Manager or %s can do this") %
                                      (rec.separation_id.hr_responsible_id.name))

            rec.write(
                {
                    "done_by": self.env.user.id,
                    "done_date": fields.Date.today(),
                    "completed": True
                }
            )

    def button_reset(self):
        for rec in self:

            current_user = self.env.user
            if not (self.user_has_groups('hr.group_hr_manager')
                    or current_user == rec.separation_id.hr_responsible_id):
                raise ValidationError(_("You are not allowed to do this. Only HR Manager or %s can do this") %
                                      (rec.separation_id.hr_responsible_id.name))

            if rec.employee_id.state != 'joined':
                raise ValidationError(_("You cannot do this after the probation period started"))

            rec.write(
                {
                    "done_by": False,
                    "done_date": False,
                    "completed": False
                }
            )

    checklist_id = fields.Many2one("hr.employee.checklist", string="Checklist", required=True)
    notes = fields.Text(string="Notes", required=False)
    done_by = fields.Many2one("res.users", "Processed By")
    done_date = fields.Date(string="Processed On")
    completed = fields.Boolean(string="Completed")

    employee_id = fields.Many2one("hr.employee", string="Employee", ondelete='cascade')
