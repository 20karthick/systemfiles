from odoo import fields, api, models

from datetime import timedelta


class Regular(models.Model):
    _inherit = 'hr.attendance'

    regularization = fields.Boolean(string="Regularization")
    regularization_id = fields.Many2one("attendance.regular", string="Regularization ID")

    # Cron job to auto checkout attendance
    @api.model
    def _auto_checkout_attendance(self):

        # Check for open attendances
        open_attendance_ids = self.env['hr.attendance'].search(
            [
                ('check_in', '!=', False),
                ('check_out', '=', False)
            ]
        )
        for att in open_attendance_ids:
            att.write({
                'check_out': att.check_in + timedelta(seconds=1)
            })