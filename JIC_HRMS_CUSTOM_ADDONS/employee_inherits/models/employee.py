from odoo import api, fields, models, tools, _
from odoo.osv import expression
from odoo.http import request
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date, timedelta, time
from dateutil.relativedelta import relativedelta
import base64
from io import BytesIO
import xlrd


class HrContractInherits(models.Model):
    _inherit = 'hr.contract'

    misc_allowance = fields.Monetary(string="Misc.Allowance")
    variable_inc = fields.Monetary(string="Variable Inc")
    arrears = fields.Monetary(string="Arrears")
    other_earnings = fields.Monetary(string="Other Earnings")
    incentive = fields.Monetary(string="Incentive")
    gmi_release = fields.Monetary(string="GMI Release")
    wage = fields.Monetary('Basic', help="Employee's monthly gross wage.")
    meal_allowance = fields.Monetary(string="Meal Coupon Allowance", help="Meal Coupon Allowance")
    travel_allowance = fields.Monetary(string="Leave Travel Allowance", help="Leave Travel allowance")
    conveyance_allowance = fields.Monetary(string="Conveyance Allowance", help="Conveyance Allowance")
    child_education_allowance = fields.Monetary(string="Child Education Allowance", help="Child Education Allowance")
    fuel_allowance_reimbursement = fields.Monetary(string="Fuel Allowance Reimbursement", help="Fuel Allowance Reimbursement")
    special_allowance = fields.Monetary(string="Special Allowance", help="Special Allowance")
    wwf_employee = fields.Monetary(string="WWF Employee", help="WWF Employee")
    esi_employee = fields.Monetary(string="ESI Employee", help="ESI Employee")
    pf_employee = fields.Monetary(string="PF Employee", help="PF Employee")
    tds = fields.Monetary(string="TDS", help="TDS")
    meal_coupon_allowance_deduction = fields.Monetary(string="Meal Coupon Allowance Deduction", help="Meal Coupon Allowance Deduction")
    gross_salary = fields.Monetary(string="Gross Salary", compute='_compute_gross_salary')

    def _compute_gross_salary(self):
        salary = 0.0
        for rec in self:
            salary = rec.wage + rec.hra + rec.travel_allowance + rec.meal_allowance + rec.medical_allowance + rec.conveyance_allowance \
                     + rec.child_education_allowance + rec.fuel_allowance_reimbursement + rec.special_allowance
            rec.gross_salary = salary







class ResumeLineInherit(models.Model):
    _inherit = 'hr.resume.line'

    resume = fields.Many2many('ir.attachment',  string="Resume Attachment", copy=False)


class ResUsersInheritsUserGroup(models.Model):
    _inherit = 'res.users'

    @api.model
    def user_group_access(self):

        active_id = self.env['res.users'].browse(self.env.context.get('active_ids'))
        for user in active_id:
            if not user.has_group('employee_inherits.employee_rbac'):
                user.write({'groups_id': [(4, self.env.ref('employee_inherits.employee_rbac').id)]})
            if not user.has_group('hr.group_hr_user'):
                user.write({'groups_id': [(4, self.env.ref('hr.group_hr_user').id)]})
        return


class InheritsHrAttendance(models.Model):
    _inherit = 'hr.attendance'

    emp_code = fields.Char('Employee ID', compute='_compute_employee_code')
    # first_half_status = fields.Char('First Half Status', size=20)
    # second_half_status = fields.Char('Second Half Status', size=20)
    first_half_status = fields.Selection([('present', 'PRESENT'),
                               ('week_off', 'WEEK OFF'),
                               ('casual_leave', 'CASUAL LEAVE'),
                               ('sick_leave', 'SICK LEAVE'),
                               ('lop', 'LOP')], string="First Half Status")
    second_half_status = fields.Selection([('present', 'PRESENT'),
                               ('week_off', 'WEEK OFF'),
                               ('casual_leave', 'CASUAL LEAVE'),
                               ('sick_leave', 'SICK LEAVE'),
                               ('lop', 'LOP')], string="Second Half Status")
    status = fields.Selection([('draft', 'Draft'),
         ('approve', 'Approved'),
         ('rejected', 'Rejected')], default='draft', string="Status")
    remarks = fields.Char('Remarks', size=20)

    def _compute_employee_code(self):
        for emp in self:
            if emp.employee_id:
                emp.emp_code = emp.employee_id.emp_code

    @api.constrains('check_in', 'check_out')
    def _check_validity_check_in_check_out(self):
        """ verifies if check_in is earlier than check_out. """
        for attendance in self:
            if attendance.check_in and attendance.check_out:
                if attendance.check_out < attendance.check_in:
                    raise ValidationError(_('%s "Check Out - %s" time cannot be earlier than "Check In - %s" time.') % (attendance.emp_code, attendance.check_out, attendance.check_in ))


class AttendanceImport(models.TransientModel):
    _name = 'attendance.import'
    _description = 'Attendance Data Import'

    upload_file = fields.Binary(string="Upload File")


    def button_submit(self):
        print("Running")
        data = base64.b64decode(self.upload_file)
        with open('/tmp/' + 'Sheet1', 'wb') as file:
            file.write(data)
        xl_workbook = xlrd.open_workbook(file.name)
        sheet_names = xl_workbook.sheet_names()
        xl_sheet = xl_workbook.sheet_by_name(sheet_names[0])
        # Number of columns
        num_cols = xl_sheet.ncols
        headers = []
        header_fields = []
        for col_idx in range(0, num_cols):
            cell_obj = xl_sheet.cell(0, col_idx)
            cell_value = cell_obj.value.strip()
            headers.append(cell_value)
            if cell_value == 'Employee ID':
                header_fields.append('emp_code')
            elif cell_value == 'Check In':
                header_fields.append('check_in')
            elif cell_value == 'Check Out':
                header_fields.append('check_out')

        import_data = []
        for row_idx in range(1, xl_sheet.nrows):  # Iterate through rows
            row_dict = {}
            for col_idx in range(0, num_cols):  # Iterate through columns
                cell_obj = xl_sheet.cell(row_idx, col_idx)
                row_dict[header_fields[col_idx]] = cell_obj.value
            import_data.append(row_dict)
        for data in import_data:
            if not data['emp_code']:
                raise ValidationError(_('please check your data list "Employee ID" missed some record'))
            if not data['check_in']:
                raise ValidationError(_('please check your data list "Check In" missed some record'))
            if not data['check_out']:
                raise ValidationError(_('please check your data list "Check Out" missed some record'))

        for row in import_data:
            attendance = self.env['hr.attendance']
            employee_id = self.env['hr.employee'].search([('emp_code', '=', row['emp_code'])])
            print("Record Details", type(row['emp_code']), type(row['check_in']), type(row['check_out']))
            if employee_id:
                checkin = (datetime.strptime(row['check_in'], '%Y-%m-%d %H:%M:%S') + relativedelta(hours=-5, minutes=-30)).strftime('%Y-%m-%d %H:%M:%S')
                checkout = (datetime.strptime(row['check_out'], '%Y-%m-%d %H:%M:%S') + relativedelta(hours=-5, minutes=-30)).strftime('%Y-%m-%d %H:%M:%S')
                checkin_time = (datetime.strptime(row['check_in'], '%Y-%m-%d %H:%M:%S') + relativedelta(hours=-5,minutes=-30)).strftime('%H:%M')
                checkout_time = (datetime.strptime(row['check_out'], '%Y-%m-%d %H:%M:%S') + relativedelta(hours=-5,minutes=-30)).strftime('%H:%M')
                attendance.create({'employee_id': employee_id.id,
                                   'emp_code': row['emp_code'],
                                   'check_in': checkin,
                                   'check_out': checkout,
                                   # 'check_in_time': float(ch_in),
                                   # 'check_out_time': float(ch_out),
                                   })

                
