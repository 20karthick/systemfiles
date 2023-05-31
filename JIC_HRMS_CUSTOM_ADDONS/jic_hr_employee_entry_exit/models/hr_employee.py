from datetime import date
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import date, timedelta


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def button_probation(self):
        for rec in self:

            # Check for user privilege
            current_user = self.env.user
            if not (self.user_has_groups('hr.group_hr_manager')
                    or self.user_has_groups('hr.group_hr_user')):
                raise UserError(_("You are not allowed to do this. Only HR Manager or HR Executives can do this"))

            for checklist in rec.checklist_ids:
                if not checklist.completed:
                    raise UserError(_("Please complete the checklist and try again"))

            if not rec.contract_id:
                raise UserError(_("Please create an active contract for the employee %s")%(rec.name))

            if not rec.probation_period:
                raise UserError(_("Please set probation period for the employee %s")%(rec.name))

            rec.contract_id.probation_start_date = fields.Date.today()
            rec.contract_id.probation_end_date = fields.Date.today() + timedelta(days=int(rec.probation_period or 0))
            rec.state = "probation"

    def button_start_employment(self):
        for rec in self:

            rec.contract_id.probation_end_date = fields.Date.today()
            rec.state = "employment"

    def fetch_checklist(self):
        for rec in self:
            checklist_ids = self.env['hr.employee.checklist'].search(
                [
                    ("type", "=", "onboarding"),
                ],
                order='sequence asc'
            )
            vals = []
            if checklist_ids:
                for check in checklist_ids:
                    vals.append((0, 0, {
                        "checklist_id": check.id
                    }))
            rec.checklist_ids = vals

    state = fields.Selection(
        [
            ("joined","Joined"),
            ("probation","On Probation"),
            ("employment","Employment"),
            ("notice_period","Notice Period"),
            ("resigned","Resigned"),
            ("terminated","Terminated")
        ], string="Status", default="joined", required=True
    )

    checklist_ids = fields.One2many("hr.employee.checklist.onboarding", "employee_id")

    @api.model_create_multi
    def create(self, vals):
        employee = super(HrEmployee, self).create(vals)
        employee.fetch_checklist()
        return employee
