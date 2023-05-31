from odoo import models, fields, api


class HREmployeeDependent(models.Model):

    _name = 'hr.employee.dependent'

    name = fields.Char(string="Name", required=True)
    relationship = fields.Selection(
        [
            ("father","Father"),
            ("mother","Mother"),
            ("spouse","Spouse"),
            ("daughter","Daughter"),
            ("son", "Son"),
            ("father_in_law","Father in Law"),
            ("mother_in_law", "Mother in Law")
        ], string="Relationship", required=True
    )
    dob = fields.Date(string="DOB", required=True)
    nationality_id = fields.Many2one("res.country", string="Nationality", required=True)
    telephone = fields.Char(string="Telephone")

    employee_id = fields.Many2one("hr.employee", string="Employee", ondelete="cascade")
