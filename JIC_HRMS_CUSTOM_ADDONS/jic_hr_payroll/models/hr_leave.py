from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    @api.model_create_multi
    def create(self, vals_list):
        if not self._context.get('leave_fast_create'):
            for values in vals_list:
                employee_id = values.get('employee_id', False)
                leave_type_id = values.get('holiday_status_id')

                employee_obj_id = self.env['hr.employee'].browse(employee_id)
                leave_type_obj_id = self.env['hr.leave.type'].browse(leave_type_id)

                # Probation Validation

                is_under_probation = True if employee_obj_id.state == 'probation' else False
                if is_under_probation and not leave_type_obj_id.allow_during_probation:
                    raise ValidationError(
                        _("You are under the probation period and %s is not allowed during probation")
                        %leave_type_obj_id.name)

        return super(HrLeave, self).create(vals_list)