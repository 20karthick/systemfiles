from datetime import date
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from num2words import num2words
import base64


class HrApplicant(models.Model):
    _inherit = 'hr.applicant'

    probation_period = fields.Integer(string="Probation Period in Days", tracking=True)
    notice_period = fields.Integer(string="Notice Period in Days", tracking=True)
    parent_id = fields.Many2one("hr.employee", string="Manager")
    signed_by = fields.Many2one("hr.employee", string="Signed By")
    work_location_id = fields.Many2one("hr.work.location", string="Work Location")
    sign_and_return_date = fields.Date(string="Sign and Return On")

    def create_employee_from_applicant(self):
        """ Create an hr.employee from the hr.applicants """
        if not self.stage_id.hired_stage:
            raise ValidationError(_("You cannot create employee at this stage. \n"
                                    "Please proceed to contract sign off and try again"))
        ret = super(HrApplicant, self).create_employee_from_applicant()

        resume_list = []
        for resume_line in self.resume_line_ids:
            resume_list.append(
                (0, 0, {
                    "name": resume_line.name,
                    "date_start": resume_line.date_start,
                    "date_end": resume_line.date_end,
                    "description": resume_line.description,
                    "line_type_id": resume_line.line_type_id.id,
                    "display_type": resume_line.display_type
                })
            )

        skill_list = []
        for skill_line in self.applicant_skill_ids:
            skill_list.append(
                (0, 0, {
                    "skill_id": skill_line.skill_id.id,
                    "skill_level_id": skill_line.skill_level_id.id,
                    "skill_type_id": skill_line.skill_type_id.id,
                    "level_progress": skill_line.level_progress,
                })
            )

        ret['context'].update(
            {
                "default_probation_period": self.probation_period,
                "default_notice_period": self.notice_period,
                "default_resume_line_ids": resume_list,
                "default_employee_skill_ids": skill_list,
                "default_parent_id": self.parent_id and self.parent_id.id or False,
                "default_work_location_id": self.work_location_id and self.work_location_id.id or False,
            }
        )
        return ret

    def _get_report_base_filename_recruitment(self):
        self.ensure_one()
        return 'Offer Letter - %s' % (self.partner_name)

    def _convert_number_to_words(self, number):
        return num2words(number, lang='en').title() or ''

    def send_mail_offer_letter(self):
        """
        This is to send offer letter to the employee
        :return:
        """
        for rec in self:
            rec.send_offer_letter_mail_to_candidate()

    def send_offer_letter_mail_to_candidate(self):

        self.ensure_one()

        # Attachment Creation
        report_template_id = self.env.ref(
            'jic_hr_employee_entry_exit.action_hr_employee_offer_letter')._render_qweb_pdf(self.id)
        data_record = base64.b64encode(report_template_id[0])
        ir_values = {
            'name': "Offer Letter - %s"%(self.partner_name),
            'type': 'binary',
            'datas': data_record,
            'store_fname': data_record,
            'mimetype': 'application/x-pdf',
        }
        data_id = self.env['ir.attachment'].create(ir_values)

        # Get Template to render
        template = self.env.ref('jic_hr_employee_entry_exit.email_template_employee_offer_letter', False)

        # Add attachment to template
        template.attachment_ids = [(6, 0, [data_id.id])]

        if template.lang:
            lang = template._render_lang(self.ids)[self.id]
        ctx = {
            'default_model': 'hr.applicant',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template),
            'default_template_id': template.id,
            'default_composition_mode': 'comment',
            #'custom_layout': "mail.mail_notification_paynow",
            'force_email': True,
            #'model_description': self.with_context(lang=lang).type_name,
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'name': _('Offer Letter'),
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }


class ApplicantGetRefuseReason(models.TransientModel):
    _inherit = 'applicant.get.refuse.reason'

    def action_refuse_reason_apply(self):

        ret = super(ApplicantGetRefuseReason, self).action_refuse_reason_apply()
        for rec in self:
            for applicant in rec.applicant_ids:
                if applicant.emp_id:
                    raise ValidationError(
                        _(
                            "Employee is already created for this record - %s. You cannot refuse this."
                        )
                        %(applicant.emp_id.emp_code)
                    )
        return ret
