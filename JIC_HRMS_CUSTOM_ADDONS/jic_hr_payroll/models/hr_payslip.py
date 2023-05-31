from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

import base64
from itertools import groupby
from datetime import datetime
import time
from dateutil.relativedelta import relativedelta


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    payslip_day_ids = fields.One2many('hr.payslip.day', 'payslip_id')

    def get_attendance_based_lop(self):
        amount = 0
        if self.payslip_day_ids:
            amount = sum([
                a.amount for a in self.payslip_day_ids.filtered(
                    lambda a:a.status in ['half_day_lop']
                )
            ])
        return amount

    def update_attendance_lop_to_input_lines(self):
        """
        this is to update attendance shortage input amount once after excuse the lines
        by hr user after loadig the line. Must acll from excuse button and revert button
        :return:
        """
        total_deduction = sum(
            [
                a.amount for a in self.payslip_day_ids.filtered(
                    lambda a: a.status == 'half_day_lop'
                )
            ]
        ) or 0

        for line in self.input_line_ids:
            if line.code == 'ATTSHORT':
                line.amount = total_deduction
        return True

    @api.model
    def get_inputs(self, contracts, date_from, date_to):
        """
        Normally this method returns list of inputs that are linked with salary rule.
        Here we add the amount also with this
        :param contracts:
        :param date_from:
        :param date_to:
        :return:
        """
        ret = super(HrPayslip, self).get_inputs(contracts, date_from, date_to)

        ########################### For Extra Inputs #####################

        extra_input_ids = self.env['hr.employee.extra.input'].search(
            [
                ('effective_date', '>=', date_from),
                ('effective_date', '<=', date_to),
                ('employee_id', '=', self.employee_id.id),
                ('payslip_id', '=', False),
                ('employee_request_id.state', '=', 'approved')
            ]
        )

        # Process list and merge duplicates
        for code, value in groupby(extra_input_ids, lambda a: a.employee_request_id.input_category_id.code):
            lines = list(value)

            for ip in ret:
                if ip.get('code') == code:
                    ip.update(
                        {
                            'amount': sum([a.amount for a in lines]),
                            'extra_input_ids': [(6, 0, [a.id for a in lines])]
                        }
                    )

                if ip.get('code') == 'ATTSHORT':
                    ip.update(
                        {
                            'amount': self.get_attendance_based_lop(),
                        }
                    )
        ########################### For Overtime Inputs #####################

        overtime_ids = self.env['hr.overtime.request'].search(
            [
                ('overtime_date', '>=', date_from),
                ('overtime_date', '<=', date_to),
                ('employee_id', '=', self.employee_id.id),
                ('payslip_id', '=', False),
                ('state', '=', 'approved')
            ]
        )
        # Process list and merge duplicates
        for code, value in groupby(overtime_ids, lambda a: a.rule_id.code):
            lines = list(value)

            for ip in ret:
                if ip.get('code') == code:
                    ip.update(
                        {
                            'amount': sum([a.settlement_amount for a in lines]),
                            'overtime_input_ids': [(6, 0, [a.id for a in lines])]
                        }
                    )
        return ret

    def action_payslip_done(self):
        """
        When confirming payslip we need to link payslip id with extra input line to block
        if from adding on another payslip.
        :return:
        """
        ret = super(HrPayslip, self).action_payslip_done()
        for rec in self:
            for input_line in rec.input_line_ids:
                if input_line.extra_input_ids:
                    input_line.extra_input_ids.write({'payslip_id': rec.id})
                    # Trigger execute action
                    input_line.extra_input_ids.mapped('employee_request_id').action_execute()
                if input_line.overtime_input_ids:
                    input_line.overtime_input_ids.write({'payslip_id': rec.id})
                    # Trigger execute action
                    input_line.overtime_input_ids.action_execute()
        return ret

    def action_payslip_cancel(self):
        ret = super(HrPayslip, self).action_payslip_cancel()
        for rec in self:
            for input_line in rec.input_line_ids:
                if input_line.extra_input_ids:
                    # Trigger execute action
                    input_line.extra_input_ids.mapped('employee_request_id').action_revert_payslip()
                if input_line.overtime_input_ids:
                    # Trigger execute action
                    input_line.overtime_input_ids.action_revert_payslip()
        return ret

    def _get_payslip_report_data(self):
        """
        This is a helper method to plot data on payslip
        :return: dict of payslip data
        """
        emp_id = self.employee_id
        contract_id = self.contract_id
        total_earnings = 0.0
        total_deductions = 0.0
        dummy_earnings = 0
        dummy_deductions = 0

        total_days = sum([a.number_of_days for a in self.worked_days_line_ids]) or 0
        loss_of_pay_days = sum([a.number_of_days for a in self.worked_days_line_ids if a.code in ['UNPAID', 'SANDWICH', 'DELAYED', 'UNPAIDHALF']]) or 0
        paid_days = total_days - loss_of_pay_days

        category_ids = self.line_ids
        basic_salary = sum(category_ids.filtered(lambda a: a.code == 'BASIC').mapped("total"))
        gross_salary = sum(category_ids.filtered(lambda a: a.code == 'GROSS').mapped("total"))
        net_salary = sum(category_ids.filtered(lambda a: a.code == 'NET').mapped("total"))

        earnings_list = []
        for earn in category_ids.filtered(lambda a: a.category_id.code in ['ALW', 'BASIC']):
            earnings_list.append({"name": earn.name, "amount": earn.amount})
            total_earnings += earn.amount

        deductions_list = []
        for ded in category_ids.filtered(lambda a: a.category_id.code == 'DED'):
            deductions_list.append({"name": ded.name, "amount": ded.amount})
            total_deductions += ded.amount

        if len(earnings_list) < len(deductions_list):
            dummy_earnings = len(deductions_list) - len(earnings_list)
        else:
            dummy_deductions = len(earnings_list) - len(deductions_list)
        return {
            "employee_name": emp_id.name,
            "joining_date": contract_id.probation_start_date,
            "employee_code": emp_id.emp_code,
            "total_days": sum([a.number_of_days for a in self.worked_days_line_ids]) or 0,
            "designation": emp_id.job_id.name,
            "loss_of_pay": sum([a.number_of_days for a in self.worked_days_line_ids if a.code in ['UNPAID', 'SANDWICH', 'DELAYED', 'UNPAIDHALF']]) or 0,
            "department": contract_id.department_id.name,
            "paid_days": paid_days or 0,
            "earned_leave": 0, # Todo
            "grade": emp_id.grade_id and emp_id.grade_id.name or '', # ToDo
            "basic_salary": basic_salary,
            "gross_salary": gross_salary,
            "net_salary": net_salary,
            "earnings_list": earnings_list,
            "deductions_list": deductions_list,
            "earnings_total_amount": total_earnings,
            "deductions_total_amount": total_deductions,
            "dummy_earnings": dummy_earnings,
            "dummy_deductions": dummy_deductions,
        }

    def send_mail_payslip(self):
        """
        This is to send payslip to the employee
        :return:
        """
        for rec in self:
            rec.send_payslip_mail_to_employee()

    def send_payslip_mail_to_employee(self):

        self.ensure_one()

        # Attachment Creation
        report_template_id = self.env.ref('hr_payroll_community.action_report_payslip')._render_qweb_pdf(self.id)
        data_record = base64.b64encode(report_template_id[0])
        ir_values = {
            'name': "Payslip - %s"%(self.employee_id.name),
            'type': 'binary',
            'datas': data_record,
            'store_fname': data_record,
            'mimetype': 'application/x-pdf',
        }
        data_id = self.env['ir.attachment'].create(ir_values)

        # Get Template to render
        template = self.env.ref('jic_hr_payroll.email_template_employee_payslip', False)

        # Add attachment to template
        template.attachment_ids = [(6, 0, [data_id.id])]

        if template.lang:
            lang = template._render_lang(self.ids)[self.id]
        ctx = {
            'default_model': 'hr.payslip',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template),
            'default_template_id': template.id,
            'default_composition_mode': 'comment',
            #'custom_layout': "mail.mail_notification_paynow",
            'force_email': True,
            #'model_description': self.with_context(lang=lang).type_name,
        }
        active_ids = self.env.context.get("active_ids")
        if active_ids and len(active_ids) > 1:
            message_composer = self.env['mail.compose.message'].with_context(
                default_use_template=bool(template),
                force_email=True, mail_notify_author=True,
            ).create({
                'res_id': self.id,
                'template_id': template and template.id or False,
                'model': 'hr.payslip',
                'composition_mode': 'comment'})
            update_values = \
            message_composer._onchange_template_id(template.id, 'comment', 'hr.payslip', self.id)['value']
            message_composer.write(update_values)
            message_composer._action_send_mail()
            return True

        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }

    def fetch_payslip_days(self):
        """
        Button method to fetch payslip days based on attendances
        :return:
        """
        for rec in self:
            if rec.state not in ['draft','verify']:
                raise UserError(_("The Payslip must be in 'Draft' or 'Verified' stages to update Payslip Days - %s")%(rec.name))
            if rec.employee_id and rec.contract_id and rec.date_from and rec.date_to:

                # Date field validations
                date_from = rec.date_from
                date_to = rec.date_to
                contract = rec.contract_id

                if contract.date_start and contract.date_start >= date_from:
                    date_from = contract.date_start
                if contract.date_end and contract.date_end <= date_to:
                    date_to = contract.date_end

                report_wiz_id = self.env['hr.attendance.report.wizard'].create({
                    "date_from": date_from,
                    "date_to": date_to,
                    "employee_id": rec.employee_id.id
                })
                date_list, attendance_lines, employees_list = report_wiz_id.get_data_to_plot()
                day_lines = []
                for line in attendance_lines:
                    if attendance_lines[line] and attendance_lines[line][0]:
                        ln = attendance_lines[line][0]
                        data = {
                                "day": ln.get("date"),
                                "check_in": ln.get("in_time")[10:],
                                "check_out": ln.get("out_time")[10:],
                                "break_hrs": ln.get("break_time"),
                                "short_hrs": ln.get("shortage_hours"),
                                "late_in": str(ln.get("late_hr")) + ":" + str(ln.get("late_min")),
                                "early_out": str(ln.get("early_hr")) + ":" + str(ln.get("early_min")),
                                "net_hrs": ln.get("net_time"),
                                "leave_hrs": ln.get("leave_hours"),
                                "calendar_hrs": ln.get("calendar_hours"),
                                "timesheet_hrs": ln.get("approved_timesheet_hours"),
                                "leave_status": ln.get("attendance_status"),
                                "grace_period": ln.get("grace_period"),
                                "max_allowed_exceptions": ln.get("max_allowed_exceptions"),
                                "holiday": ln.get("holiday"),
                                "overtime_hrs": ln.get("overtime_hours"),
                                "legal_hrs": ln.get("legal_hours")
                            }

                        day_lines.append(
                            (0, 0, data)
                        )
                rec.payslip_day_ids = False
                rec.payslip_day_ids = day_lines

    def button_trigger_employee_onchange(self):
        """
        This is just for a refresh purpose only for employee onchange.
        :return:
        """
        for rec in self:
            rec.onchange_employee()

    @api.onchange('employee_id', 'date_from', 'date_to')
    def onchange_employee(self):
        ret = super(HrPayslip, self).onchange_employee()
        self.fetch_payslip_days()
        self.update_attendance_lop_to_input_lines()

    def button_refresh(self):
        # Todo Remove this method
        return True


# Changed By karthick

class ResourceCalendar(models.Model):
    """ Calendar model for a resource. It has

     - attendance_ids: list of resource.calendar.attendance that are a working
                       interval in a given weekday.
     - leave_ids: list of leaves linked to this calendar. A leave can be general
                  or linked to a specific resource, depending on its resource_id.

    All methods in this class use intervals. An interval is a tuple holding
    (begin_datetime, end_datetime). A list of intervals is therefore a list of
    tuples, holding several intervals of work or leaves. """
    _inherit = "resource.calendar"
    _description = "Resource Working Time"

    def _work_intervals_batch(self, start_dt, end_dt, resources=None, domain=None, tz=None):
        """ Return the effective work intervals between the given datetimes. """
        if not resources:
            resources = self.env['resource.resource']
            resources_list = [resources]
        else:
            resources_list = list(resources)
        date_from_start = start_dt + relativedelta(months=-1, day=26)
        date_to_end = end_dt + relativedelta(day=25)
        attendance_intervals = self._attendance_intervals_batch(start_dt, end_dt, resources, tz=tz)
        leave_intervals = self._leave_intervals_batch(date_from_start, date_to_end, resources, domain, tz=tz)
        return {
            r.id: (attendance_intervals[r.id] - leave_intervals[r.id]) for r in resources_list
        }
