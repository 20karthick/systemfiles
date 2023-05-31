from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    paid_percentage = fields.Float(string='Paid %')
    allow_during_probation = fields.Boolean(string='Allow During Probation')
    exclude_from_gratuity = fields.Boolean(string='Exclude From Gratuity')
    exclude_from_vaccation = fields.Boolean(string='Exclude From Vacation Accruals', default=True)
    exclude_from_air_ticket = fields.Boolean(string='Exclude From Air Ticket Accruals', default=True)
    include_ess = fields.Boolean(string='Include in ESS')
    mandatory_role_delegation = fields.Integer(string='No of Days for Mandatory Role Delegation')
    min_cuttoff_days_for_salary_advance = fields.Integer(string='Min Cutoff Days for Salary Advance')


