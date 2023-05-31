# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, SUPERUSER_ID


class PayslipSendMailWiz(models.TransientModel):
    _name = 'payslip.send.mail.wiz'
    _description = 'Payslip Send Mail Wizard'

    def send_payslip_via_mail(self):
        active_ids = self._context.get('active_ids', [])
        payslip_ids = self.env['hr.payslip'].browse(active_ids)
        payslip_ids.send_mail_payslip()