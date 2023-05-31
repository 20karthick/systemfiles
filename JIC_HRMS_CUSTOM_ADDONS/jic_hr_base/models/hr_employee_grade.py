from odoo import models, fields, api


class HREmployeeGrade(models.Model):

    _name = 'hr.employee.grade'

    name = fields.Char(string="Grade", required=True)