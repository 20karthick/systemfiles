from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta, time
import pytz
from odoo.addons.resource.models.resource import float_to_time


class HrOvertimeConf(models.Model):

    _name = 'hr.overtime.conf'

    name = fields.Float(string="Compensation %", required=True)
    overtime_type = fields.Selection(
        [
            ("normal_ot", "Normal OT"),
            ("friday_ot", "Friday OT"),
            ("holiday_ot", "Holiday OT"),
            ("sunday_ot", "Sunday OT"),
        ]
        , string="Overtime Type", default="normal_ot", required=True)
    department_id = fields.Many2one("hr.department", string="Department")


class HrOvertimeRequest(models.Model):

    _name = 'hr.overtime.request'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.model
    def _default_employee_id(self):
        employee = self.env.user.employee_id
        if not employee:
            raise ValidationError(_('The current user has no related employee. Please, create one.'))
        return employee

    @api.depends('employee_id')
    def _compute_from_employee_id(self):
        for req in self:
            req.manager_id = req.employee_id.parent_id.id

    @api.depends('employee_id')
    def _compute_department_id(self):
        for req in self:
            if req.employee_id:
                req.department_id = req.employee_id.department_id
            else:
                req.department_id = False

    @api.depends('employee_id')
    def _get_hr_responsible(self):
        for rec in self:
            active_contracts = self.env['hr.contract'].search(
                [
                    ("state", "=", "open"),
                    ("employee_id", "=", rec.employee_id.id)
                ]
            )
            if active_contracts:
                rec.hr_responsible_id = active_contracts[0].hr_responsible_id.id

    @api.depends('amount')
    def _compute_ot_string(self):
        for rec in self:
            if rec.amount:
                if rec.amount and rec.amount <= 23:
                    rec.amount_float_time = float_to_time(round(abs(float(rec.amount)), 2)).strftime("%H:%M") or "00:00"
                else:
                    rec.amount_float_time = "00:00"

    @api.depends('overtime_date', 'employee_id')
    def _compute_worked_hours(self):
        for rec in self:
            if rec.overtime_date and rec.employee_id:

                # Attendance Pick

                date_to_check_start = fields.Datetime.from_string(rec.overtime_date.strftime("%Y-%m-%d 00:00:00"))
                date_to_check_stop = date_to_check_start + timedelta(days=1, seconds=-1)
                # In Datetime
                day_from = datetime.combine(date_to_check_start, time.min).replace(tzinfo=pytz.UTC)
                day_to = datetime.combine(date_to_check_stop, time.max).replace(tzinfo=pytz.UTC)

                attendance_a_day_ids = self.env["hr.attendance"].search(
                    [
                        ("check_in", ">=", date_to_check_start),
                        ("check_out", "<=", date_to_check_stop),
                        ("employee_id", "=", rec.employee_id.id)
                    ]
                )
                total_worked_hours = sum(attendance_a_day_ids.mapped("worked_hours")) or 0

                # Contract hours pick

                legal = rec.employee_id.list_work_time_per_day(day_from, day_to, None)
                legal_hours = legal[0][1] if legal else 0

                rec.worked_hours = total_worked_hours
                rec.contract_hours = legal_hours
                rec.overtime_hours = (total_worked_hours - legal_hours) if total_worked_hours > legal_hours else 0
                rec.amount = (total_worked_hours - legal_hours) if total_worked_hours > legal_hours else 0

    @api.depends('contract_hours', 'overtime_date')
    def _compute_salary_rule_and_ot_type(self):
        for rec in self:
            # Check the day for normal, holiday or friday
            date_to_check_start = fields.Datetime.from_string(rec.overtime_date.strftime("%Y-%m-%d 00:00:00"))
            date_to_check_stop = date_to_check_start + timedelta(days=1, seconds=-1)
            public_holidays = rec.employee_id.list_leaves(date_to_check_start, date_to_check_stop,
                                                               calendar=rec.employee_id.contract_id.resource_calendar_id)

            holiday = False
            for day, hours, leave in public_holidays:
                if not leave.holiday_id:
                    holiday = True
            if holiday:
                rec.overtime_type = 'holiday_ot'
                rec.rule_id = self.env['hr.salary.rule'].search([('company_id', '=', rec.company_id.id), ('code', '=', 'OTHOLIDAYIND')], limit=1)
            elif rec.overtime_date.weekday() == 6:
                rec.overtime_type = 'sunday_ot'
                rec.rule_id = self.env['hr.salary.rule'].search([('company_id', '=', rec.company_id.id),('code', '=', 'OTSUNDAYIND')], limit=1)
            else:
                rec.overtime_type = 'normal_ot'
                rec.rule_id = self.env['hr.salary.rule'].search([('company_id', '=', rec.company_id.id), ('code', '=', 'OTNORMALIND')], limit=1)

            # if holiday:
            #     rec.overtime_type = 'holiday_ot'
            #     rec.rule_id = self.env.ref("jic_hr_payroll.hr_rule_overtime_holiday").id
            # elif rec.overtime_date.weekday() == 4:
            #     rec.overtime_type = 'friday_ot'
            #     rec.rule_id = self.env.ref("jic_hr_payroll.hr_rule_overtime_friday").id
            # else:
            #     rec.overtime_type = 'normal_ot'
            #     rec.rule_id = self.env.ref("jic_hr_payroll.hr_rule_overtime_normal").id

    @api.depends('overtime_type', 'amount', 'overtime_date')
    def _compute_settlement_amount(self):
        for rec in self:

            # Compute hourly rate
            one_hour_wage = rec.employee_id.contract_id.get_one_hour_wage(rec.overtime_date, rec.overtime_date)
            rate_perc = 0
            if rec.department_id:
                for ot_conf in rec.department_id.overtime_ids:
                    if ot_conf.overtime_type == rec.overtime_type:
                        rate_perc = ot_conf.name
            rec.settlement_amount = (one_hour_wage * rate_perc) / 100 * rec.amount

    name = fields.Char(string="Name", readonly=True)
    employee_id = fields.Many2one("hr.employee", string="Employee", required=True, tracking=True, copy=False,
                                  default=lambda self: self._default_employee_id(), readonly=True,
                                  states={'requested': [('readonly', False)]})
    manager_id = fields.Many2one('hr.employee', compute='_compute_from_employee_id', readonly=True,
                                 store=True, required=False)
    hr_responsible_id = fields.Many2one("res.users", string="HR Responsible", compute="_get_hr_responsible", store=True)
    department_id = fields.Many2one(
        'hr.department', compute='_compute_department_id', store=True,
        string='Department', readonly=True)
    user_id = fields.Many2one('res.users', copy=False, tracking=True, string='User',
                              related="employee_id.user_id", related_sudo=True, compute_sudo=True)
    date = fields.Date(string="Requested Date", required=True, default=fields.Date.today(), tracking=True, readonly=True)

    overtime_date = fields.Date(string="OT Date", default=fields.Date.today(),
                                required=True, readonly=True, states={'requested': [('readonly', False)]})
    worked_hours = fields.Float(string="Worked Hours", store=True, compute='_compute_worked_hours')
    contract_hours = fields.Float(string="Contract Hours", store=True, compute='_compute_worked_hours')
    overtime_hours = fields.Float(string="Overtime Hours Logged", store=True, compute='_compute_worked_hours')

    amount = fields.Float(string="OT Hours Requested", required=True, tracking=True, readonly=True,
                          states={'requested': [('readonly', False)]})
    amount_float_time = fields.Char(string="OT in String", compute='_compute_ot_string', store=True)
    settlement_amount = fields.Monetary(string="Settlement Amount",
            compute='_compute_settlement_amount', store=True, currency_field='company_currency_id')
    note = fields.Text(string="Note", tracking=True)
    company_id = fields.Many2one('res.company', required=True, readonly=True, default=lambda self: self.env.company)
    company_currency_id = fields.Many2one(related='company_id.currency_id', string='Company Currency',
                                          readonly=True, store=True,
                                          help='Utility field to express amount currency')
    overtime_type = fields.Selection(
        [
            ("normal_ot", "Normal OT"),
            ("friday_ot", "Friday OT"),
            ("holiday_ot", "Holiday OT"),
            ("sunday_ot", "Sunday OT"),
        ]
        , string="Overtime Type", compute='_compute_salary_rule_and_ot_type', store=True)
    state = fields.Selection(
        [
            ('requested', 'Requested'),
            ('validated', 'Validated'),
            ('approved', 'Approved'),
            ('executed', 'Executed'),
            ('rejected', 'Rejected')
        ], default='requested', string="Status", required=True, tracking=True
    )
    rule_id = fields.Many2one("hr.salary.rule", string="Salary Rule", compute='_compute_salary_rule_and_ot_type', store=True)

    payslip_id = fields.Many2one("hr.payslip", string="Payslip")
    payslip_status = fields.Selection(string="Payslip Status", related="payslip_id.state", store=True)

    _sql_constraints = [
        ('overtime_employee_day_uniq', 'unique (employee_id, overtime_date)', 'Overtime Date Must Be Unique Per Employee.'),
    ]

    @api.model_create_multi
    def create(self, vals):
        request = super(HrOvertimeRequest, self).create(vals)
        if not request.amount:
            raise ValidationError(_("Please select OT hours to create a request"))

        if not request.name:
            request.name = self.env[
                'ir.sequence'].next_by_code('jic.overtime.request')
        request.send_notification_mail_to_approver()
        return request

    def unlink(self):
        for ip in self:
            if ip.state != 'requested':
                raise ValidationError(_("Cannot delete record that not in state 'Requested'"))
        return super(HrOvertimeRequest, self).unlink()

    @api.returns('self', lambda value: value.id)
    def copy(self):
        raise UserError(_('You cannot duplicate overtime request.'))

    def float_to_time_excel(self, float_value):
        if float_value and float_value <= 23:
            return float_to_time(round(abs(float(float_value)), 2)).strftime("%H:%M") or "00:00"
        else:
            "00:00"

    def action_validate(self):
        """
        Manager will do approvals
        :return:
        """
        for rec in self:

            if not rec.overtime_hours:
                raise ValidationError(
                    _(
                        "There is no overtime hours found as per the records - %s - %s"
                    ) % (rec.employee_id.name, rec.overtime_date.strftime("%d %B, %Y")))

            if rec.overtime_hours < rec.amount:
                raise ValidationError(_("Total hours cannot exceed %s") % (rec.float_to_time_excel(rec.overtime_hours)))

            if not rec.hr_responsible_id:
                raise ValidationError(_("Please set HR Responsible for this employee"))

            # Check for user privilege
            current_user = self.env.user

            if not (self.user_has_groups('hr.group_hr_manager') or
                    rec.employee_id.parent_id.user_id == current_user
                    or current_user == rec.hr_responsible_id):
                raise ValidationError(_("You are not allowed to do this. Only HR Manager or %s or %s can do this") % (rec.hr_responsible_id.name, rec.employee_id.parent_id.name))

            active_contracts = self.env['hr.contract'].search(
                [
                    ("state","=","open"),
                    ("employee_id","=",rec.employee_id.id)
                ]
            )
            if not active_contracts:
                raise ValidationError(_("There is no active contracts for the employee %s") % (rec.employee_id.name))

            # Send mail to hr executive
            self.send_notification_mail_to_approver(act_type='approve')

            rec.state = 'validated'

    def action_approve(self):
        """
        HR Executive will do approvals
        :return:
        """
        for rec in self:

            if not rec.employee_id.allow_overtime:
                raise ValidationError(_("Employee %s has no rights to request for overtime compensation")%(rec.employee_id.name))

            if not rec.department_id.overtime_ids:
                raise ValidationError(_("Please configure overtime rate for this department - %s")%(rec.department_id.name))

            if rec.overtime_hours < rec.amount:
                raise ValidationError(_("Total hours cannot exceed %s")%(rec.float_to_time_excel(rec.overtime_hours)))

            if not (self.user_has_groups('hr.group_hr_manager')
                    or self.env.user == rec.hr_responsible_id):
                raise ValidationError(_("You are not allowed to do this"))

            rec.state = 'approved'

    def action_reject(self):
        for rec in self:
            rec.state = 'rejected'

    def action_draft(self):
        for rec in self:

            if not (self.user_has_groups('hr.group_hr_manager')
                    or self.env.user == rec.hr_responsible_id):
                raise ValidationError(_("You are not allowed to do this"))

            rec.state = 'requested'

    def action_execute(self):
        for rec in self:
            rec.state = 'executed'

    def action_revert_payslip(self):
        """
        When Payslip got cancelled, this will trigger
        :return:
        """
        for rec in self:
            rec.state = 'approved'

    def send_notification_mail_to_approver(self, act_type='validate'):
        template = self.env.ref('jic_hr_payroll.email_template_employee_overtime_request', False)
        partner_to = self.employee_id.parent_id.user_id.partner_id.id
        partner_to_name = self.employee_id.parent_id.user_id.partner_id.name

        if act_type == 'approve':
            partner_to = self.hr_responsible_id.partner_id.id
            partner_to_name = self.hr_responsible_id.partner_id.name
        message_composer = self.env['mail.compose.message'].with_context(
            default_use_template=bool(template),
            force_email=True, mail_notify_author=True,
            partner_to=partner_to,partner_to_name=partner_to_name
        ).create({
            'res_id': self.id,
            'template_id': template and template.id or False,
            'model': 'hr.overtime.request',
            'composition_mode': 'comment'})

        # Simulate the onchange (like trigger in form the view)
        update_values = message_composer._onchange_template_id(template.id, 'comment', 'hr.overtime.request', self.id)['value']
        message_composer.write(update_values)
        message_composer._action_send_mail()