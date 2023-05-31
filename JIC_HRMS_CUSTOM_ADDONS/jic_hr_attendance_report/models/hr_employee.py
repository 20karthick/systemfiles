from odoo import fields, api, models, _
from odoo.exceptions import ValidationError

from datetime import datetime
from dateutil.relativedelta import relativedelta
import calendar
import base64


class AllowedIPs(models.Model):
    _name = 'allowed.ips'

    ip_address = fields.Char(string='Allowed IP')
    company_id = fields.Many2one('res.company', string="Company")


class ResCompany(models.Model):
    _inherit = 'res.company'

    allowed_ips_ids = fields.One2many('allowed.ips', 'company_id')


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def button_attendance_report(self):
        if self.attendance_report_range:
            if self.attendance_report_range == 'this_month':
                date = datetime.today()
                date_from = datetime(date.year, date.month, 1).strftime("%Y-%m-%d")
                date_to = date.strftime("%Y-%m-%d")

            if self.attendance_report_range == 'last_month':
                date = (datetime.now() - relativedelta(months=1))
                date_from = datetime(date.year, date.month, 1).strftime("%Y-%m-%d")
                date_to = datetime(date.year, date.month, calendar.mdays[date.month]).strftime("%Y-%m-%d")

            report_wiz_id = self.env["hr.attendance.report.wizard"].create({
                "date_from": date_from,
                "date_to": date_to,
                "employee_id": self.id
            })
            report_wiz_id.action_download()
            return {
                "type": "ir.actions.act_url",
                "url": "/web/binary/jic_attendance_report?wizard_id=%s"
                       % (report_wiz_id.id),
                "target": "new",
                "tag": "reload",
            }

    def send_attendance_report_xlsx_mail_to_employee(self):
        self.ensure_one()

        if self.attendance_report_range == 'this_month' or self.env.context.get('force_this_month'):
            date = datetime.today()
            date_from = datetime(date.year, date.month, 1).strftime("%Y-%m-%d")
            date_to = date.strftime("%Y-%m-%d")

        else:
            date = (datetime.now() - relativedelta(months=1))
            date_from = datetime(date.year, date.month, 1).strftime("%Y-%m-%d")
            date_to = datetime(date.year, date.month, calendar.mdays[date.month]).strftime("%Y-%m-%d")

        report_wiz_id = self.env["hr.attendance.report.wizard"].create({
            "date_from": date_from,
            "date_to": date_to,
            "employee_id": self.id
        })
        report_wiz_id.action_download()

        # Attachment Creation
        ir_values = {
            'name': "AttendanceReport-%s.xlsx" % self.name,
            'type': 'binary',
            'datas': report_wiz_id.report_file,
            'store_fname': 'AttendanceReportXlsx.xlsx',
        }
        data_id = self.env['ir.attachment'].create(ir_values)

        # Get Template to render
        template = self.env.ref('jic_hr_attendance_report.email_template_employee_periodic_attendances_xlsx', False)

        # Add attachment to template
        template.attachment_ids = [(6, 0, [data_id.id])]

        if template.lang:
            lang = template._render_lang(self.ids)[self.id]
        ctx = {
            'default_model': 'hr.employee',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template),
            'default_template_id': template.id,
            'default_composition_mode': 'comment',
            'date_from': date_from,
            'date_to': date_to,
            #'custom_layout': "mail.mail_notification_paynow",
            'force_email': True,
            #'model_description': self.with_context(lang=lang).type_name,
        }
        active_ids = self.env.context.get("active_ids")
        if active_ids and len(active_ids) > 1 or self.env.context.get('force_this_month'):
            message_composer = self.env['mail.compose.message'].with_context(
                default_use_template=bool(template),
                force_email=True, mail_notify_author=True,
            ).create({
                'res_id': self.id,
                'template_id': template and template.id or False,
                'model': 'hr.employee',
                'composition_mode': 'comment'})
            update_values = \
            message_composer._onchange_template_id(template.id, 'comment', 'hr.employee', self.id)['value']
            message_composer.write(update_values)
            message_composer._action_send_mail()
            return True

        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }

    def _send_periodic_attendance_report_xlsx(self):
        """
        Calling from cron job to send mail to employees periodically
        It must return trigger mail every 3 days with datas of last one week
        :return:
        """
        for employee in self.env['hr.employee'].search(
                [
                    ('opt_for_attendance_mail','=', True)
                ]
        ):
            employee.with_context({'force_this_month': True}).send_attendance_report_xlsx_mail_to_employee()

    # This is to block attendance from other ip address

    def attendance_manual(self, next_action, entered_pin=None):
        local_context = self.env.context
        if local_context.get('ip'):
            ip = local_context.get('ip')
            allowed_ips = self.env.user.company_id.allowed_ips_ids.mapped('ip_address')
            if allowed_ips:
                if ip not in allowed_ips:
                    raise ValidationError(_("IP Access Error\n You are not allowed to perform this form the IP %s")%(ip))
        return super(HrEmployee, self).attendance_manual(next_action, entered_pin=None)