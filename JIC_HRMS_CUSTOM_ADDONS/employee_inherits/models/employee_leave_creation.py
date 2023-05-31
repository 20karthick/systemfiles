from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import float_compare, float_round

import base64
from datetime import datetime, date,time, timedelta
from pytz import utc
import calendar
from pytz import timezone
from collections import defaultdict
from dateutil.rrule import rrule, DAILY
from dateutil.relativedelta import relativedelta


class EmployeeLeaveCreation(models.Model):
    _name = 'employee.leave.creation'
    _description = 'Leave Creation'

    name = fields.Many2one('hr.employee',  required=True, string='Created Employees Name')
    employee_ids = fields.Many2many('hr.employee', required=True, string='Employees')
    date_from = fields.Date(string='Date From', required=True, help="Start date",
                            default=lambda self: fields.Date.to_string((datetime.now() + relativedelta(months=-1, day=26)).date()))
    date_to = fields.Date(string='Date To', required=True, help="End date",
                          default=lambda self: fields.Date.to_string(
                              (datetime.now() + relativedelta(day=25)).date()))


    def leave_creation(self):
        if self.employee_ids:
            for employee in self.employee_ids:
                date_from = self.date_from
                date_to = self.date_to
                attendance_id = self.env['hr.attendance'].search([('employee_id', 'in', employee.ids),
                                                                  ('check_in', '>=', date_from),
                                                                  ('check_in', '<=', date_to)])
                leaves_id = self.env['hr.leave'].search([('employee_ids', 'in', employee.id),
                                                         ('request_date_from', '>=', date_from),
                                                         ('request_date_to', '<=', date_to),
                                                         ('state', '=', 'validate')])
                leaves_type = self.env['hr.leave.type'].search([('company_id', '=', employee.company_id.id), ('code', '=', 'UNPAID')])
                payroll_date = []
                attendance_date = []
                leaves = []
                calendar = self.env['resource.calendar'].search([('id', '=', employee.resource_calendar_id.id)])

                for d in rrule(DAILY, dtstart=date_from, until=date_to):
                    payroll_day_name = d.strftime('%A')
                    if payroll_day_name != 'Sunday':
                        payroll_date.append(d.strftime("%Y-%m-%d"))
                for att in attendance_id:
                    date = att.check_in.strftime("%Y-%m-%d")
                    attendance_date.append(date)
                for leave in leaves_id:
                    leave_date_from = leave.request_date_from.strftime("%Y-%m-%d")
                    leave_date_to = leave.request_date_to.strftime("%Y-%m-%d")
                    leaves.append(leave_date_from)
                    leaves.append(leave_date_to)

                for pd in payroll_date:
                    if pd not in attendance_date:
                        if pd not in leaves:
                            date = datetime.strptime(pd, '%Y-%m-%d').date()
                            time = datetime.combine(date, datetime.min.time())
                            print("yyyyyyyy", type(date), date, time + timedelta(hours=6))
                            if employee:
                                leave = self.env['hr.leave'].create({
                                    'employee_id': employee.id,
                                    'name': 'Attendance',
                                    'holiday_type': 'employee',
                                    'mode_company_id': employee.company_id.id,
                                    'holiday_status_id': leaves_type.id,
                                    'request_date_from': time + timedelta(hours=6),
                                    'date_from': time + timedelta(hours=6),
                                    'date_to': time + timedelta(hours=15),
                                    'request_date_to': time + timedelta(hours=15),
                                    'number_of_days': 1,
                                    'state': 'draft',

                                })
                                leave._compute_date_from_to()
                                leave.action_confirm()
                                leave.action_approve()


