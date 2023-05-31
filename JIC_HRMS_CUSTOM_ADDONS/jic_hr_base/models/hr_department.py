# -*- coding: utf-8 -*-
import json

from lxml import etree
from odoo import api, fields, models, _


class HrDepartment(models.Model):
    _inherit = "hr.department"

    grace_period_in_attendance = fields.Float(string='Grace Period in Attendance')
    max_allowed_exceptions_in_month = fields.Integer(string="Max Allowed Exceptions")
