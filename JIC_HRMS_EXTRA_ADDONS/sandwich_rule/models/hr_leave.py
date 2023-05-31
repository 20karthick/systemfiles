# -*- coding: utf-8 -*-
# © 2018-Today Aktiv Software (http://aktivsoftware.com).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import calendar
import datetime
from datetime import date

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class HolidaysRequest(models.Model):
    _inherit = "hr.leave"

    sandwich_rule = fields.Boolean("Sandwich Rule")
    hr_consider_sandwich_rule = fields.Boolean("Apply Sandwich Rule", default=True)

    @api.onchange("number_of_days", "hr_consider_sandwich_rule", "date_from", "date_to")
    def check_leave_type(self):
        if (
            self.hr_consider_sandwich_rule
            and self.employee_id
            and self.number_of_days > 1
        ):
            days = set(
                [
                    calendar.day_name[int(each.dayofweek)]
                    for each in self.employee_id.resource_calendar_id.attendance_ids
                ]
            )
            leave_ids = self.env["hr.leave"].search(
                [("employee_id", "=", self.employee_id.id)]
            )
            for i in range(int(self.number_of_days) - 1):
                if (
                    calendar.day_name[
                        (self.date_from + datetime.timedelta(days=i + 1)).weekday()
                    ]
                    not in days
                ):
                    self.sandwich_rule = True
                    break
            else:
                self.sandwich_rule = False
        else:
            self.sandwich_rule = False
        if self.date_from and self.date_to:
            self.number_of_days = (self.date_to.date() - self.date_from.date()).days + 1

    @api.constrains("date_from", "date_to", "employee_id")
    def check_date_from_live(self):
        res = {}
        days = set(
            [
                calendar.day_name[int(each.dayofweek)]
                for each in self.employee_id.resource_calendar_id.attendance_ids
            ]
        )

        if self.date_from and calendar.day_name[self.date_from.weekday()] not in days:
            raise ValidationError(_("This day is already holiday."))

        if self.date_to and calendar.day_name[self.date_to.weekday()] not in days:
            raise ValidationError(_("This day is already holiday."))
