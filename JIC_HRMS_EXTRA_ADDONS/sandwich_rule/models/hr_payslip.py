from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import float_compare, float_round

import base64
from datetime import datetime, time, timedelta
from pytz import utc
import calendar
from pytz import timezone
from dateutil.relativedelta import relativedelta


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def check_for_weekend_or_public_holidays(self, date_from, date_to, public_leaves):
        missed_days = 0
        missed_dates = []
        total_days = (date_to - date_from).days
        days = set(
            [
                calendar.day_name[int(each.dayofweek)]
                for each in self.employee_id.resource_calendar_id.attendance_ids
            ]
        )
        for i in range(int(total_days) - 1):
            chk_day = date_from + timedelta(days=i + 1)

            if (
                    calendar.day_name[
                        (chk_day).weekday()
                    ]
                    not in days or chk_day.date() in [p for p in list(public_leaves.keys())]
            ):
                missed_days += 1
                missed_dates.append(chk_day.date())
        print("-------------------",missed_dates,missed_days)
        return missed_dates, missed_days

    def check_for_skipped_sandwich_dates(self, day_from, day_to, contract, triggered_days, public_leaves):
        print("GGGGGGGGGGGGGGGGGGGGGGGGG", day_from, day_to, triggered_days)
        leaves = {}
        calendar_id = contract.resource_calendar_id
        tz = timezone(calendar_id.tz)
        day_leave_intervals = contract.employee_id.list_leaves(day_from, day_to,
                    calendar=contract.resource_calendar_id, domain=[('time_type', 'in', ['leave'])])
        for day, hours, leave in day_leave_intervals:
            holiday = leave.holiday_id
            if holiday:
                current_leave_struct = leaves.setdefault(day, {
                    'name': holiday.holiday_status_id.name or _('Global Leaves'),
                    'sequence': 5,
                    'code': holiday.holiday_status_id.code or 'GLOBAL',
                    'number_of_days': 0.0,
                    'number_of_hours': 0.0,
                    'contract_id': contract.id,
                })
                current_leave_struct['number_of_hours'] += hours
                work_hours = calendar_id.get_work_hours_count(
                    tz.localize(datetime.combine(day, time.min)),
                    tz.localize(datetime.combine(day, time.max)),
                    compute_leaves=False,
                )
                if work_hours:
                    current_leave_struct['number_of_days'] += hours / work_hours

        # Adding already considered sandwich leave
        for already_triggered_unpaid_leaves in triggered_days:
            leaves.update({already_triggered_unpaid_leaves: {
                'name': _('Sandwich Leaves'),
                'sequence': 5,
                'code': 'SANDWICH',
                'number_of_days': 1.0,
                'number_of_hours': 8.0,
                'contract_id': contract.id,
            }})

            print("AAAAAAAAAAAAAAAA", already_triggered_unpaid_leaves)

        # Find missed unpaid leaves form total leave list
        missed_days = 0
        missed_dates = []
        total_days = (day_to - day_from).days
        days = set(
            [
                calendar.day_name[int(each.dayofweek)]
                for each in self.employee_id.resource_calendar_id.attendance_ids
            ]
        )
        for i in range(int(total_days) - 1):
            chk_day = day_from + timedelta(days=i + 1)
            if chk_day.date() not in triggered_days: # Skip already considered days
                if (
                        calendar.day_name[
                            (chk_day).weekday()
                        ]
                        not in days or chk_day.date() in [p for p in list(public_leaves.keys())]
                ):
                    # We got the weekends and public holidays here
                    # Now we need to check the left and right for sandwich rule
                    left_flag = False
                    right_flag = False

                    # Check left side of the day
                    left = chk_day - timedelta(days=1)
                    if left.date() in [p for p in list(leaves.keys())]:
                        left_flag = True

                    # Check right side of the day
                    right = chk_day + timedelta(days=1)
                    if right.date() in [p for p in list(leaves.keys())]:
                        right_flag = True

                    if left_flag and right_flag:
                        missed_days += 1
                        missed_dates.append(chk_day.date())
        print("-~~~~~~~~~~~~~~~~~~~~~~~~~~~~", missed_dates, missed_days)
        return missed_dates, missed_days

    # @api.model
    # def get_worked_day_lines(self, contracts, date_from, date_to):
    #     ret = super(HrPayslip, self).get_worked_day_lines(contracts, date_from, date_to)
    #     if ret:
    #         contract_id = ret[0].get('contract_id')
    #         contract = self.env['hr.contract'].browse(contract_id)
    #         day_from = datetime.combine(fields.Date.from_string(date_from), time.min)
    #         day_to = datetime.combine(fields.Date.from_string(date_to), time.max)
    #
    #         if contract.date_start and contract.date_start >= date_from:
    #             day_from = datetime.combine(fields.Date.from_string(contract.date_start), time.min)
    #         if contract.date_end and contract.date_end <= date_to:
    #             day_to = datetime.combine(fields.Date.from_string(contract.date_end), time.min)
    #
    #         ######################### Public Holidays Check #######################################3
    #         calendar = contract.resource_calendar_id
    #         tz = timezone(calendar.tz)
    #         public_leaves = {}
    #         public_holidays = contract.employee_id.list_leaves(day_from, day_to,
    #                                                            calendar=contract.resource_calendar_id)
    #         for day, hours, leave in public_holidays:
    #             holiday = leave.holiday_id
    #             if not holiday:
    #                 current_leave_struct = public_leaves.setdefault(day, {
    #                     'name': holiday.holiday_status_id.name or _('Global Leaves'),
    #                     'sequence': 5,
    #                     'code': holiday.holiday_status_id.code or 'GLOBAL',
    #                     'number_of_days': 0.0,
    #                     'number_of_hours': 0.0,
    #                     'contract_id': contract.id,
    #                 })
    #                 current_leave_struct['number_of_hours'] += hours
    #                 work_hours = calendar.get_work_hours_count(
    #                     tz.localize(datetime.combine(day, time.min)),
    #                     tz.localize(datetime.combine(day, time.max)),
    #                     compute_leaves=False,
    #                 )
    #                 if work_hours:
    #                     current_leave_struct['number_of_days'] += hours / work_hours
    #         # Remove all public holidays which is not having full day IMPORTANT
    #         for pub in public_leaves:
    #             if public_leaves[pub].get('number_of_days') != 1:
    #                 del public_leaves[pub]
    #         #################################################################
    #
    #         leave_intervals = contract.employee_id.list_leaves_only(day_from, day_to,
    #                                                                calendar=contract.resource_calendar_id)
    #         sandwich_leave_days = []
    #         triggered_days = []
    #         for start, stop, leave in leave_intervals:
    #             #hours = (stop - start).total_seconds() / 3600
    #             if leave.holiday_id.holiday_status_id.code == 'UNPAID':
    #                 if leave.holiday_id.sandwich_rule:
    #                     missed_dates, missed_days = self.check_for_weekend_or_public_holidays(start, stop, public_leaves)
    #                     if missed_days:
    #                         sandwich_leave_days.append(missed_days)
    #                         triggered_days.extend(missed_dates)
    #
    #         employee_missed_dates, employee_missed_days = self.check_for_skipped_sandwich_dates(day_from, day_to, contract, triggered_days, public_leaves)
    #         if employee_missed_days:
    #             sandwich_leave_days.append(employee_missed_days)
    #             triggered_days.extend(employee_missed_dates)
    #
    #         if sandwich_leave_days:
    #             ret.append(
    #                 {
    #                     'name': 'Sandwich days applied',
    #                     'sequence': 100,
    #                     'code': 'SANDWICH',
    #                     'number_of_days': sum(sandwich_leave_days),
    #                     'number_of_hours': sum(sandwich_leave_days) * 8,
    #                     'contract_id': contract.id,
    #                     'notes': ' ,'.join([a.strftime('%d %B, %Y') for a in triggered_days])
    #                 }
    #             )
    #
    #     return ret

    # CHANGED BY KARTHICK
    @api.model
    def get_worked_day_lines(self, contracts, date_from, date_to):
        print("################3333333333333333333")
        ret = super(HrPayslip, self).get_worked_day_lines(contracts, date_from, date_to)
        if ret:
            contract_id = ret[0].get('contract_id')
            contract = self.env['hr.contract'].browse(contract_id)
            day_from = datetime.combine(fields.Date.from_string(date_from), time.min)
            day_to = datetime.combine(fields.Date.from_string(date_to), time.max)

            if contract.date_start and contract.date_start >= date_from:
                day_from = datetime.combine(fields.Date.from_string(contract.date_start), time.min)
            if contract.date_end and contract.date_end <= date_to:
                day_to = datetime.combine(fields.Date.from_string(contract.date_end), time.min)

            ######################### Public Holidays Check #######################################3
            calendar = contract.resource_calendar_id
            tz = timezone(calendar.tz)
            public_leaves = {}
            date_from_start = date_from + relativedelta(months=-1, day=26)
            date_to_end = date_to + relativedelta(day=25)
            day_from_start = datetime.combine(fields.Date.from_string(date_from_start), time.min)
            day_to_end = datetime.combine(fields.Date.from_string(date_to_end), time.max)
            public_holidays = contract.employee_id.list_leaves(day_from_start, day_to_end,
                                                               calendar=contract.resource_calendar_id)
            for day, hours, leave in public_holidays:
                holiday = leave.holiday_id
                if not holiday:
                    print("OOOOOOOOOOOOOOOOOOO")
                    current_leave_struct = public_leaves.setdefault(day, {
                        'name': holiday.holiday_status_id.name or _('Global Leaves'),
                        'sequence': 5,
                        'code': holiday.holiday_status_id.code or 'GLOBAL',
                        'number_of_days': 0.0,
                        'number_of_hours': 0.0,
                        'contract_id': contract.id,
                    })
                    current_leave_struct['number_of_hours'] += hours
                    work_hours = calendar.get_work_hours_count(
                        tz.localize(datetime.combine(day, time.min)),
                        tz.localize(datetime.combine(day, time.max)),
                        compute_leaves=False,
                    )
                    if work_hours:
                        current_leave_struct['number_of_days'] += hours / work_hours
            # Remove all public holidays which is not having full day IMPORTANT
            for pub in public_leaves:
                if public_leaves[pub].get('number_of_days') != 1:
                    del public_leaves[pub]
            #################################################################

            leave_intervals = contract.employee_id.list_leaves_only(day_from_start, day_to_end,
                                                                    calendar=contract.resource_calendar_id)
            sandwich_leave_days = []
            triggered_days = []
            for start, stop, leave in leave_intervals:
                #hours = (stop - start).total_seconds() / 3600
                if leave.holiday_id.holiday_status_id.code == 'UNPAID':
                    if leave.holiday_id.sandwich_rule:
                        print("::::::::::::::::::::")
                        missed_dates, missed_days = self.check_for_weekend_or_public_holidays(start, stop, public_leaves)
                        if missed_days:
                            sandwich_leave_days.append(missed_days)
                            triggered_days.extend(missed_dates)
            print("WWWWWWWWWWWWWWWWWWW", triggered_days)

            employee_missed_dates, employee_missed_days = self.check_for_skipped_sandwich_dates(day_from_start, day_to_end, contract, triggered_days, public_leaves)
            if employee_missed_days:
                # sandwich_leave_days.append(employee_missed_days)
                # triggered_days.extend(employee_missed_dates)
                print("LLLLLLLLLLLLLLL",triggered_days, employee_missed_dates, employee_missed_days)

            if sandwich_leave_days:
                ret.append(
                    {
                        'name': 'Sandwich days applied',
                        'sequence': 100,
                        'code': 'SANDWICH',
                        'number_of_days': sum(sandwich_leave_days),
                        'number_of_hours': sum(sandwich_leave_days) * 8,
                        'contract_id': contract.id,
                        'notes': ' ,'.join([a.strftime('%d %B, %Y') for a in triggered_days])
                    }
                )

        return ret


class HrPayslipWorkedDays(models.Model):
    _inherit = 'hr.payslip.worked_days'

    notes = fields.Text(string="Extra Notes")


class ResourceMixin(models.AbstractModel):
    _inherit = "resource.mixin"

    def list_leaves_only(self, from_datetime, to_datetime, calendar=None, domain=None):
        """
            This is to get the leaves for this employee on this contract
            and avoid attendance. A copy of 'list_leaves' in mixin
        """
        resource = self.resource_id
        calendar = calendar or self.resource_calendar_id

        # naive datetimes are made explicit in UTC
        if not from_datetime.tzinfo:
            from_datetime = from_datetime.replace(tzinfo=utc)
        if not to_datetime.tzinfo:
            to_datetime = to_datetime.replace(tzinfo=utc)

        #attendances = calendar._attendance_intervals_batch(from_datetime, to_datetime, resource)[resource.id]
        leaves = calendar._leave_intervals_batch(from_datetime, to_datetime, resource, domain)[resource.id]
        return leaves
