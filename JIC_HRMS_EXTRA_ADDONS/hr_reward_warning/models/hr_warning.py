from datetime import datetime

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HrAnnouncementTable(models.Model):
    _name = 'hr.announcement'
    _description = 'HR Announcement'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.depends('employee_ids', 'department_ids', 'position_ids', 'is_announcement')
    def _get_partners(self):
        for rec in self:
            partner_ids = False
            user_ids = False
            employee_ids = self.env['hr.employee']

            if rec.is_announcement:
                employee_ids = self.env['hr.employee'].search(
                    [
                        ('state','not in', ['resigned', 'terminated'])
                    ]
                )

            if rec.employee_ids:
                employee_ids += rec.employee_ids
            if rec.department_ids:
                employee_ids += self.env['hr.employee'].search([('department_id','in', rec.department_ids.ids)])
            if rec.position_ids:
                employee_ids += self.env['hr.employee'].search([('job_id', 'in', rec.position_ids.ids)])

            if employee_ids:
                partner_ids = employee_ids.mapped('user_id').mapped('partner_id')
                user_ids = employee_ids.mapped('user_id')

            rec.partner_ids = partner_ids
            rec.user_ids = user_ids

    name = fields.Char(string='Code No:', help="Sequence Number of the Announcement")
    announcement_reason = fields.Text(string='Title', states={'draft': [('readonly', False)]}, required=True,
                                      readonly=True, help="Announcement Subject")
    state = fields.Selection([('draft', 'Draft'), ('to_approve', 'Waiting For Approval'),
                              ('approved', 'Approved'), ('rejected', 'Refused'), ('expired', 'Expired')],
                             string='Status',  default='draft',
                             track_visibility='always')
    requested_date = fields.Date(string='Requested Date', default=datetime.now().strftime('%Y-%m-%d'),
                                 help="Create Date of Record")
    attachment_id = fields.Many2many('ir.attachment', 'doc_warning_rel', 'doc_id', 'attach_id4',
                                     string="Attachment", help='You can attach the copy of your Letter')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.user.company_id, readonly=True, help="Login user Company")
    is_announcement = fields.Boolean(string='Is general Announcement?', help="To set Announcement as general announcement")
    announcement_type = fields.Selection([('employee', 'By Employee'), ('department', 'By Department'), ('job_position', 'By Job Position')])
    employee_ids = fields.Many2many('hr.employee', 'hr_employee_announcements', 'announcement', 'employee',
                                    string='Employees', help="Employee's which want to see this announcement")
    department_ids = fields.Many2many('hr.department', 'hr_department_announcements', 'announcement', 'department',
                                      string='Departments', help="Department's which want to see this announcement")
    position_ids = fields.Many2many('hr.job', 'hr_job_position_announcements', 'announcement', 'job_position',
                                    string='Job Positions',help="Job Position's which want to see this announcement")
    announcement = fields.Html(string='Letter', states={'draft': [('readonly', False)]}, readonly=True, help="Announcement Content")
    date_start = fields.Date(string='Start Date', default=fields.Date.today(), required=True, help="Start date of "
                                                                                                   "announcement want"
                                                                                                   " to see")
    date_end = fields.Date(string='End Date', default=fields.Date.today(), required=True, help="End date of "
                                                                                               "announcement want too"
                                                                                               " see")
    partner_ids = fields.Many2many('res.partner', string='Partners', compute='_get_partners', store=True)
    user_ids = fields.Many2many('res.users', string='Users', compute='_get_partners', store=True)

    def reject(self):
        self.state = 'rejected'

    def approve(self):
        self.state = 'approved'

    def sent(self):
        self.state = 'to_approve'

    @api.constrains('date_start', 'date_end')
    def validation(self):
        if self.date_start > self.date_end:
            raise ValidationError("Start date must be less than End Date")

    @api.model
    def create(self, vals):
        if vals.get('is_announcement'):
            vals['name'] = self.env['ir.sequence'].next_by_code('hr.announcement.general')
        else:
            vals['name'] = self.env['ir.sequence'].next_by_code('hr.announcement')
        return super(HrAnnouncementTable, self).create(vals)

    def unlink(self):
        for record in self:
            if record.state == 'approved' and record.partner_ids:
                raise ValidationError(_("You cannot delete this as the record is approved"))
        super(HrAnnouncementTable, self).unlink()

    def get_expiry_state(self):
        """
        Function is used for Expiring Announcement based on expiry date
        it activate from the crone job.

        """
        now = datetime.now()
        now_date = now.date()
        ann_obj = self.search([('state', '!=', 'rejected')])
        for recd in ann_obj:
            if recd.date_end < now_date:
                recd.write({
                    'state': 'expired'
                })

    def send_announcement_mail_to_employee(self):

        self.ensure_one()

        # Get Template to render
        template = self.env.ref('hr_reward_warning.email_template_company_announcements', False)

        if template.lang:
            lang = template._render_lang(self.ids)[self.id]
        ctx = {
            'default_model': 'hr.announcement',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template),
            'default_template_id': template.id,
            'default_composition_mode': 'comment',
            'default_partner_ids': self.partner_ids.ids,
            #'custom_layout': "mail.mail_notification_paynow",
            'force_email': True,
            #'model_description': self.with_context(lang=lang).type_name,
        }

        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }
