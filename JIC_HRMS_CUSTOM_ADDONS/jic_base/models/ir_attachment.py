import math

from odoo import api, models, fields, api, _
from odoo.exceptions import UserError, ValidationError

allowed_mimetypes = [
    'image/jpeg', 'application/javascript', 'application/msword', 'application/pdf',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel', 'image/jpeg', 'image/png', 'text/calendar', 'text/css', 'text/csv', 'text/plain','application/octet-stream', 'image/svg+xml'
]


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    size = fields.Char("File Size", compute="_compute_convert_size", store=True)
    size_in_mb = fields.Integer("File Size in Mb", compute="_compute_convert_size", store=True)

    @api.depends("file_size")
    def _compute_convert_size(self):
        """Compute for convert file size"""
        for rec in self:
            if rec.file_size == 0:
                return "0B"
            size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
            i = int(math.floor(math.log(rec.file_size, 1024)))
            p = math.pow(1024, i)
            s = round(rec.file_size / p, 2)
            rec.size = "%s %s" % (s, size_name[i])
            rec.size_in_mb = rec.file_size / 1024 / 1024


    # @api.constrains('mimetype')
    # def check_file_type(self):
    #     for rec in self:
    #         if rec.mimetype and rec.mimetype not in allowed_mimetypes:
    #             raise UserError(_(
    #                 "Sorry, You are not allowed to upload this file. "
    #                 "Please contact your system administrator, "
    #                 "if you think this is an error."))
