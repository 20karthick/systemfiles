from datetime import date
from odoo import models, fields, api


class EmployeeChecklist(models.Model):
    _name = "hr.employee.checklist"
    _order = "sequence"

    name = fields.Char(string="Checklist Name", required=True)
    checklist_type_id = fields.Many2one('hr.employee.checklist.type', string='Checklist Type')
    type = fields.Selection(related='checklist_type_id.type', string="Type", store=True)
    sequence = fields.Integer(string="Sequence", required=True)


class EmployeeChecklistType(models.Model):
    _name = "hr.employee.checklist.type"

    name = fields.Char(string="Type Name", required=True)
    type = fields.Selection(
        [
            ('resignation', 'Resignation'),
            ('fired', 'Termination'),
            ('absconding', 'Absconding'),
            ('death', 'Death'),
            ('article41a', 'Article 41a'),
            ('retirement', 'Retirement'),
            ('onboarding', 'Onboarding')
        ], default="resignation", string="Type", required=True
    )
    settlement_conf_ids = fields.One2many('hr.employee.settlement.conf', 'checklist_type_id')


class HrEmployeeSettlementConf(models.Model):
    _name = "hr.employee.settlement.conf"

    from_year = fields.Integer(string="From Year (Incl)", required=True)
    to_year = fields.Integer(string="To Year (Excl)", required=True)
    days = fields.Integer(string="Days in an Year", required=True)
    paid_days = fields.Integer(string="Paid Days", required=True)
    pay_percentage = fields.Float(string="Pay Percentage")

    checklist_type_id = fields.Many2one('hr.employee.checklist.type', string='Checklist Type')