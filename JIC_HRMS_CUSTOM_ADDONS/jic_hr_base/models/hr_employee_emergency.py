from odoo import models, fields, api


class HREmployeeEmergency(models.Model):

    _name = 'hr.employee.emergency'

    name = fields.Char(string="Contact Name", required=True)
    type = fields.Selection(
        [
            ("local","Local"),
            ("overseas","Overseas"),
        ], string="Relationship", default='local', required=True
    )
    relationship = fields.Selection(
        [
            ("father", "Father"),
            ("mother", "Mother"),
            ("spouse", "Spouse"),
            ("daughter", "Daughter"),
            ("son", "Son"),
            ("father_in_law", "Father in Law"),
            ("mother_in_law", "Mother in Law")
        ], string="Relationship", required=True
    )
    number_1 = fields.Char(string="Number 1", required=True)
    number_2 = fields.Char(string="Number 2")

    employee_id = fields.Many2one("hr.employee", string="Employee", ondelete="cascade")