from odoo import models, fields, api, _

import base64


class HrPayslipDay(models.Model):
    _name = 'hr.payslip.day'

    payslip_id = fields.Many2one('hr.payslip', string='Payslip', ondelete='cascade')

    employee_id = fields.Many2one('hr.employee', related='payslip_id.employee_id', store=True)
    contract_id = fields.Many2one('hr.contract', related='payslip_id.contract_id', store=True)
    date_from = fields.Date(related='payslip_id.date_from', store=True)
    date_to = fields.Date(related='payslip_id.date_to', store=True)
    need_to_log_timesheet = fields.Boolean(related="employee_id.need_to_log_timesheet", store=True)

    day = fields.Date(string="Day")
    weekday = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday'),
    ], string="Weekday", compute="_get_weekday", store=True)
    check_in = fields.Char(string="IN")
    check_out = fields.Char(string="OUT")
    break_hrs = fields.Float(string="Break")
    short_hrs = fields.Float(string="Shortage")
    late_in = fields.Char(string="Late IN")
    early_out = fields.Char(string="Early OUT")
    timesheet_hrs = fields.Float(string="Timesheet Hrs")
    net_hrs = fields.Float(string="Net Hrs")
    leave_hrs = fields.Float(string="Leave Hrs")
    calendar_hrs = fields.Float(string="Calendar Hrs")
    legal_hrs = fields.Float(string="Legal Hrs")
    overtime_hrs = fields.Float(string="OverTime Hrs")
    holiday = fields.Boolean(string="Is Holiday")
    leave_status = fields.Selection(
        [
            ('PRESENT','Present'),
            ('OFF','Off'),
            ('LEAVE-H','Half Day Leave'),
            ('LEAVE-F','Full Day Leave')
        ], default='PRESENT', string='Leave Status'
    )
    status = fields.Selection(
        [
            ('normal','Normal'),
            ('excused','Excused'),
            ('half_day_lop', 'Half Day Cut'),
        ], default='normal', string="Final Status", compute="_get_final_status", store=True
    )
    time_short = fields.Boolean(string="TimeShort", compute="_get_shortages", store=True)
    timesheet_short = fields.Boolean(string="TimesheetShort", compute="_get_shortages", store=True)
    excused = fields.Boolean(string="Excused")
    amount = fields.Float(string='Amount', compute='_get_half_pay_amount', store=True)
    grace_period = fields.Float(string='Grace Period')
    max_allowed_exceptions = fields.Integer(string="Max Allowed Exceptions")
    excused_by = fields.Many2one("hr.employee", string="Excused By")

    def button_excuse(self):
        for rec in self:
            rec.excused = True
            rec.payslip_id.update_attendance_lop_to_input_lines()
            rec.excused_by = self.env.user.employee_id.id

    def button_revert(self):
        for rec in self:
            rec.payslip_id.update_attendance_lop_to_input_lines()
            rec.excused = False

    @api.depends("day")
    def _get_weekday(self):
        for rec in self:
            if rec.day:
                rec.weekday = str(rec.day.weekday())

    @api.depends("contract_id", "payslip_id")
    def _get_half_pay_amount(self):
        for rec in self:
            if rec.contract_id and rec.payslip_id:
                full_day_pay = rec.contract_id.get_single_day_wage(
                    rec.payslip_id.date_from, rec.payslip_id.date_from
                )
                rec.amount = self.env.company.currency_id.round(full_day_pay / 2)

    @api.depends("short_hrs", "leave_status", "timesheet_hrs", "calendar_hrs", "leave_hrs")
    def _get_shortages(self):
        for rec in self:

            if rec.timesheet_hrs < rec.legal_hrs:
                rec.timesheet_short = True
            else:
                rec.timesheet_short = False

            if (rec.net_hrs + rec.grace_period) < rec.legal_hrs:
                rec.time_short = True
            else:
                rec.time_short = False

            # Some users don't need to log timesheet
            if not rec.need_to_log_timesheet:
                rec.timesheet_short = False

    @api.depends("time_short", "timesheet_short", "leave_status", "excused")
    def _get_final_status(self):
        for rec in self:
            if rec.excused:
                rec.status = 'excused'
            elif rec.leave_status in ['PRESENT', 'LEAVE-H']:
                if rec.time_short or rec.timesheet_short:
                    rec.status = 'half_day_lop'
            else:
                rec.status = 'normal'
