# -*- coding: utf-8 -*-
import base64
from io import BytesIO
import os
from odoo.exceptions import ValidationError

from odoo import api, fields, models, _, SUPERUSER_ID


class BulkExtraInputRequestsWizard(models.TransientModel):
    _name = 'bulk.extra.inputs.wiz'
    _description = 'Common Data Import Wizard'

    employee_ids = fields.Many2many("hr.employee", string="Employee(s)", required=True)
    date = fields.Date(string="Effective Date", default=fields.Date.today(), required=True)
    amount = fields.Float(string="Amount", required=True)
    input_id = fields.Many2one("hr.employee.extra.input.category", required=True,
                               domain=[('restrict_from_user_request','=',False)])
    department_id = fields.Many2one("hr.department", string="Department")
    category_id = fields.Many2one(related="input_id.category_id")
    note = fields.Text(string="Notes", required=True)


    @api.onchange("department_id")
    def onchange_department_id(self):
        if self.department_id:
            self.employee_ids |= self.env['hr.employee'].search([('department_id','=', self.department_id.id)])

    def action_confirm(self):
        for employee in self.employee_ids:
            data = {
                "input_category_id": self.input_id.id,
                "employee_id": employee.id,
                "date": self.date,
                "amount": self.amount,
            }
            request_id = self.env['hr.employee.input.requests'].create(data)

            self.env['hr.employee.extra.input'].create(
                {
                    "amount": self.amount,
                    "effective_date": self.date,
                    "employee_request_id": request_id.id,
                }
            )
            request_id.sudo().action_validate()
            request_id.sudo().action_approve()
        return {'type': 'ir.actions.act_window_close'}