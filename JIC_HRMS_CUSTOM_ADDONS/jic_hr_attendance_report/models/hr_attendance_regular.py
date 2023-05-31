from odoo import fields, api, models, _
from odoo.exceptions import ValidationError, UserError


class Regular(models.Model):
    _name = 'attendance.regular'
    _rec_name = 'name'
    _description = 'Approval Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.model
    def _default_employee_id(self):
        employee = self.env.user.employee_id
        if not employee:
            raise ValidationError(_('The current user has no related employee. Please, create one.'))
        return employee

    name = fields.Char(string="Name")
    reg_category = fields.Many2one('reg.categories', string='Regularization Category', required=True,
                                   help='Choose the category of attendance regularization',
                                   track_visibility='onchange')
    from_date = fields.Datetime(string='From Date', required=True, help='Start Date', readonly=True,
                                track_visibility='onchange')
    to_date = fields.Datetime(string='To Date', required=True, help='End Date',
                              track_visibility='onchange')
    reg_reason = fields.Text(string='Reason', required=True, help='Reason for the attendance regularization')
    employee_id = fields.Many2one("hr.employee", string="Employee", required=True, tracking=True,
                                  default=lambda self: self._default_employee_id())
    user_id = fields.Many2one('res.users', copy=False, tracking=True, string='User',
                              related="employee_id.user_id", related_sudo=True, compute_sudo=True)
    hr_responsible_id = fields.Many2one(related="employee_id.contract_id.hr_responsible_id", store=True)
    state_select = fields.Selection([('draft', 'Draft'), ('requested', 'Requested'), ('reject', 'Rejected'),
                                     ('approved', 'Approved')
                                     ], default='draft', track_visibility='onchange', string='State',
                                    help='State')
    regulated_hours = fields.Float(string='Total Hours', compute='_compute_regulated_hours', store=True, readonly=True)
    company_id = fields.Many2one('res.company', required=True, readonly=True, default=lambda self: self.env.company)

    @api.model_create_multi
    def create(self, vals):

        for val in vals:
            if val.get('from_date') and val.get('to_date'):
                if val.get('from_date')[:10] != val.get('to_date')[:10]:
                    raise ValidationError(_("The timeframe must be belongs to the same day"))

        request = super(Regular, self).create(vals)

        if not request.name:
            request.name = self.env[
                'ir.sequence'].next_by_code('jic.employee.regularization.request')
        return request

    @api.depends('from_date', 'to_date')
    def _compute_regulated_hours(self):
        for attendance in self:
            if attendance.to_date and attendance.from_date:
                delta = attendance.to_date - attendance.from_date
                attendance.regulated_hours = delta.total_seconds() / 3600.0
            else:
                attendance.regulated_hours = False

    def submit_reg(self):
        self.ensure_one()
        self.send_notification_mail_to_manager()
        self.sudo().write({
            'state_select': 'requested'
        })
        return True

    def regular_approval(self):
        if self.from_date.date() != self.to_date.date():
            raise ValidationError(_("The timeframe must be belongs to the same day"))
        self.write({
            'state_select': 'approved'
        })
        vals = {
            'check_in': self.from_date,
            'check_out': self.to_date,
            'employee_id': self.employee_id.id,
            'regularization': True,
            'regularization_id': self.id
        }
        approve = self.env['hr.attendance'].sudo().create(vals)
        return

    def regular_rejection(self):
        self.write({
            'state_select': 'reject'
        })
        return

    def send_notification_mail_to_manager(self):
        """
        Notification mail to reporting manager
        :param act_type:
        :return:
        """
        template = self.env.ref('jic_hr_attendance_report.email_template_employee_regularization', False)

        partner_to = self.hr_responsible_id.partner_id.id
        partner_to_name = self.hr_responsible_id.partner_id.name
        message_composer = self.env['mail.compose.message'].with_context(
            default_use_template=bool(template),
            force_email=True, mail_notify_author=True,
            partner_to=partner_to,partner_to_name=partner_to_name
        ).create({
            'res_id': self.id,
            'template_id': template and template.id or False,
            'model': 'attendance.regular',
            'composition_mode': 'comment'})

        # Simulate the onchange (like trigger in form the view)
        update_values = message_composer._onchange_template_id(template.id, 'comment', 'attendance.regular', self.id)['value']
        message_composer.write(update_values)
        message_composer._action_send_mail()


class Category(models.Model):
    _name = 'reg.categories'
    _rec_name = 'type'

    type = fields.Char(string='Category', help='Type of regularization')