from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

from datetime import datetime


class HREmployeeInputsRequest(models.Model):
    _name = 'hr.employee.input.requests'
    _description = "Employee Allowance/Deduction Request"
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

    name = fields.Char(string="Name", readonly=True)
    employee_id = fields.Many2one("hr.employee", string="Employee", required=True, tracking=True,copy=False,
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
    date = fields.Date(string="Date", required=True, default=fields.Date.today(), tracking=True, readonly=True,
                                  states={'requested': [('readonly', False)]})
    input_category_id = fields.Many2one("hr.employee.extra.input.category", string="Input", required=True, tracking=True, readonly=True,
                                  states={'requested': [('readonly', False)]})
    category_id = fields.Many2one(related="input_category_id.category_id", store=True, tracking=True)
    amount = fields.Float(string="Amount", required=True, tracking=True, readonly=True,
                                  states={'requested': [('readonly', False)]})
    note = fields.Text(string="Note", tracking=True)
    company_id = fields.Many2one('res.company', required=True, readonly=True, default=lambda self: self.env.company)
    state = fields.Selection(
        [
            ('requested','Requested'),
            ('validated', 'Validated'),
            ('approved','Approved'),
            ('executed','Executed'),
            ('rejected','Rejected')
        ], default='requested', string="Status", required=True, tracking=True
    )
    input_line_ids = fields.One2many('hr.employee.extra.input', 'employee_request_id', readonly=True,
                                  states={'requested': [('readonly', True)], 'validated': [('readonly', False)]})

    @api.model_create_multi
    def create(self, vals):
        request = super(HREmployeeInputsRequest, self).create(vals)
        if not request.name:
            type_request = request.input_category_id.code
            ded_code = request.input_category_id.category_id.code
            request.name = type_request + "/" + ded_code + "/" + self.env[
                'ir.sequence'].next_by_code('jic.payslip.input.request')
        request.send_notification_mail_to_approver()
        return request

    def unlink(self):
        for ip in self:
            if ip.state != 'requested':
                raise ValidationError(_("Cannot delete record that not in state 'Requested'"))
        return super(HREmployeeInputsRequest, self).unlink()

    @api.returns('self', lambda value: value.id)
    def copy(self):
        raise UserError(_('You cannot duplicate an extra input request.'))

    @api.depends("input_line_ids.payslip_status")
    def _compute_executed(self):
        for rec in self:
            payslip_status = [a.payslip_status for a in rec.input_line_ids]
            if payslip_status and len(list(set(payslip_status))) == 1 and payslip_status[0] == 'done':
                rec.executed = True
                rec.state = 'executed'
            else:
                rec.executed = False

    def action_validate(self):
        """
        Manager will do approvals
        :return:
        """
        for rec in self:

            if rec.amount < sum([a.amount for a in rec.input_line_ids]):
                raise ValidationError(_("Total amount exceeded"))

            if not rec.hr_responsible_id:
                raise ValidationError(_("Please set HR Responsible for this employee - %s")%(rec.employee_id.name))

            # Check for user privilege
            current_user = self.env.user

            if not (self.user_has_groups('hr.group_hr_manager') or
                    rec.employee_id.parent_id.user_id == current_user
                    or current_user == rec.hr_responsible_id):
                raise ValidationError(_("You are not allowed to do this. Only HR Manager or %s or %s can do this")%(rec.hr_responsible_id.name, rec.employee_id.parent_id.name))

            active_contracts = self.env['hr.contract'].search(
                [
                    ("state","=","open"),
                    ("employee_id","=",rec.employee_id.id)
                ]
            )
            if not active_contracts:
                raise ValidationError(_("There is no active contracts for the employee %s")%(rec.employee_id.name))

            # rec.activity_schedule(
            #     'mail.mail_activity_data_todo', datetime.now(),
            #     _('Pending Approval - %s - %s' % (rec.employee_id.name, rec.name)),
            #     user_id=rec.hr_responsible_id.id or self.env.uid)

            # Send mail to hr executive
            self.send_notification_mail_to_approver(act_type='approve')

            rec.state = 'validated'

    def action_approve(self):
        """
        HR Executive will do approvals
        :return:
        """
        for rec in self:

            if rec.amount < sum([a.amount for a in rec.input_line_ids]):
                raise ValidationError(_("Total amount exceeded"))

            if not (self.user_has_groups('hr.group_hr_manager')
                    or self.env.user == rec.hr_responsible_id):
                raise ValidationError(_("You are not allowed to do this"))

            if not rec.input_line_ids or not sum([a.amount or 0 for a in rec.input_line_ids]):
                raise ValidationError(_("Must allocate the amount to payroll date. Please create input lines - %s")%(rec.name))

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
            payslip_status = [a.payslip_status for a in rec.input_line_ids]
            if payslip_status and len(list(set(payslip_status))) == 1 and payslip_status[0] == 'done':
                rec.state = 'executed'

    def action_revert_payslip(self):
        """
        When Payslip got cancelled, this will trigger
        :return:
        """
        for rec in self:
            rec.state = 'approved'

    def send_notification_mail_to_approver(self, act_type='validate'):
        template = self.env.ref('jic_hr_payroll.email_template_employee_input_request', False)
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
            'model': 'hr.employee.input.requests',
            'composition_mode': 'comment'})

        # Simulate the onchange (like trigger in form the view)
        update_values = message_composer._onchange_template_id(template.id, 'comment', 'hr.employee.input.requests', self.id)['value']
        message_composer.write(update_values)
        message_composer._action_send_mail()

    @api.constrains("amount", "input_line_ids.amount")
    def _check_amounts(self):
        for rec in self:
            if rec.amount < sum([a.amount for a in rec.input_line_ids]):
                raise ValidationError(_("Cannot process amount more than %s") % (rec.amount))


class HREmployeeExtraInputCategory(models.Model):

    _name = 'hr.employee.extra.input.category'

    name = fields.Char(string="Name", required=True)
    code = fields.Char(related="rule_id.code", string="Payslip Code", store=True)
    category_id = fields.Many2one(related="rule_id.category_id", string="Category", store=True)
    rule_id = fields.Many2one('hr.salary.rule', string='Salary Rule', required=False)
    restrict_from_user_request = fields.Boolean(string="Restrict From User Request")


class HREmployeeExtraInput(models.Model):

    _name = 'hr.employee.extra.input'

    name = fields.Char(string="Code", related="employee_request_id.name", store=True)
    employee_id = fields.Many2one(related="employee_request_id.employee_id", string="Employee", store=True)
    user_id = fields.Many2one('res.users', copy=False, string='User',
                              default=lambda self: self.env.user, store=True)
    date = fields.Date(related="employee_request_id.date",string="Date", store=True)
    amount = fields.Float(string="Amount", required=True)
    effective_date = fields.Date(string="Effective Date", required=True,
                                 help="This is the date to consider on payslip")
    payslip_id = fields.Many2one("hr.payslip", string="Payslip")
    payslip_status = fields.Selection(string="Payslip Status", related="payslip_id.state", store=True)

    employee_request_id = fields.Many2one('hr.employee.input.requests', string='Request')
    rule_id = fields.Many2one(related="employee_request_id.input_category_id.rule_id", store=True)


class HrSalaryRule(models.Model):

    _inherit = 'hr.salary.rule'

    extra_input_category_ids = fields.One2many('hr.employee.extra.input.category', 'rule_id')


class HrPayslipInput(models.Model):
    _inherit = 'hr.payslip.input'

    extra_input_ids = fields.Many2many('hr.employee.extra.input', string='Extra Input')
    overtime_input_ids = fields.Many2many('hr.overtime.request', string='Overtime Input')

