# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class HrTimeSheetSubmitWizard(models.TransientModel):
    _name = 'hr.timesheet.submit.wizard'
    _description = 'Submit Wizard for Time sheets'

    def action_submit(self):
        """
        This is to submit all the time sheets selected
        :return:
        """
        for timesheet in self.env['hr.timesheet.entry'].browse(
                self.env.context.get('active_ids', [])):
            timesheet.action_submit()


class HrTimeSheetApprovalWizard(models.TransientModel):
    _name = 'hr.timesheet.approval.wizard'
    _description = 'Approval Wizard for Time sheets'

    def action_approve(self):
        """
        This is to approve all the time sheets selected
        :return:
        """
        for timesheet in self.env['hr.timesheet.entry'].browse(
                self.env.context.get('active_ids', [])):
            timesheet.action_approve()


class HrTimeSheetDraftWizard(models.TransientModel):
    _name = 'hr.timesheet.draft.wizard'
    _description = 'Draft Wizard for Time sheets'

    def action_draft(self):
        """
        This is to reset to draft all the time sheets selected
        :return:
        """
        for timesheet in self.env['hr.timesheet.entry'].browse(
                self.env.context.get('active_ids', [])):
            timesheet.action_draft()
