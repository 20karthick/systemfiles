from odoo import models, fields, api


class ResCompany(models.Model):

    _inherit = 'res.company'

    # Offer letter
    section_1 = fields.Text(string="Offer Letter Sec-1")
    section_2 = fields.Text(string="Offer Letter Sec-2")
    section_3 = fields.Text(string="Offer Letter Sec-3")
    section_4 = fields.Text(string="Offer Letter Sec-4")