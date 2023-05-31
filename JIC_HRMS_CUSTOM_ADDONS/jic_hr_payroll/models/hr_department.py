from odoo import models, fields, api, _


class HrDepartment(models.Model):

    _inherit = 'hr.department'

    overtime_ids = fields.One2many('hr.overtime.conf', 'department_id')

