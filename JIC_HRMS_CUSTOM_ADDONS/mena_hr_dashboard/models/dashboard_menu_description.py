from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, UserError
import base64
import io


class DashboardMenuDescription(models.Model):
    _name = 'dashboard.menu.description'
    _description = 'Menu Description'

    menu_id = fields.Many2one('ir.ui.menu', domain=[('parent_id', '=', False)], string='Menu Name')
    name = fields.Char('Name', related="menu_id.name")
    description = fields.Char('Description', size=173)
    image = fields.Binary(string="Image")


    @api.constrains('menu_id')
    def _check_unique_name(self):
        if self.menu_id:
            if len(self.search([('menu_id', '=', self.menu_id.id)])) > 1:
                raise ValidationError("Menu Description Already Exists.")

    def write(self, vals):
        result = super(DashboardMenuDescription, self).write(vals)
        menu_list = self.env['ir.ui.menu'].search([('id', '=', self.menu_id.id)])
        for menu in menu_list:
            menu.description = False
            menu.image = None
            menu.description = self.description
            menu.write({'image': self.image})
            # menu.image = base64.b64decode(self.image)
        return result