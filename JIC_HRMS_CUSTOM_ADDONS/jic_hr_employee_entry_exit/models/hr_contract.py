from datetime import date
from odoo import models, fields, api


class HrContract(models.Model):
    _inherit = 'hr.contract'

    def _get_total_years_of_service(self, date_end):
        if date_end and self.date_start:
            from_d = fields.Date.from_string(self.date_start)
            to_d = fields.Date.from_string(date_end)
            return (to_d - from_d).days / 365

    probation_period = fields.Integer(related="employee_id.probation_period", store=True, string="Probation Period in Days", tracking=True)
    probation_start_date = fields.Date(string="Probation Start Date", tracking=True)
    probation_end_date = fields.Date(string="Probation End Date", tracking=True)

    notice_period = fields.Integer(related="employee_id.notice_period", store=True, string="Notice Period in Days", tracking=True)
    notice_start_date = fields.Date(string="Notice Period Start Date", tracking=True)
    notice_end_date = fields.Date(string="Notice Period End Date", tracking=True)


