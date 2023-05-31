# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    weekday = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday'),
    ], string="Weekday", compute="_get_weekday", store=True)

    @api.depends("date")
    def _get_weekday(self):
        for rec in self:
            if rec.date:
                rec.weekday = str(rec.date.weekday())



