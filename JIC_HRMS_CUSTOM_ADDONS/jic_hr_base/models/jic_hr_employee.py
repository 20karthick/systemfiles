from odoo import models, fields, api

class ResCompanyInherits(models.Model):
    _inherit = 'res.company'

    enmfi = fields.Boolean(string="Indian Company", help="Non mandatory fields hide for indian company.")
    kuwait_company = fields.Boolean(string="Kuwait Company", help="Non mandatory fields hide for Kuwait company.")

class HREmployeePublic(models.Model):

    _inherit = 'hr.employee.public'

    emp_code = fields.Char(related="employee_id.emp_code", string="Employee ID", readonly=True)
    state = fields.Selection(related="employee_id.state", readonly=True)
    exit_date = fields.Date(related="employee_id.exit_date", readonly=True)
    probation_period = fields.Integer(related="employee_id.probation_period", readonly=True)
    notice_period = fields.Integer(related="employee_id.notice_period", readonly=True)
    grade_id = fields.Many2one(related="employee_id.grade_id", readonly=True)
    opt_for_attendance_mail = fields.Boolean(related="employee_id.opt_for_attendance_mail", readonly=True)

    religion = fields.Selection(related="employee_id.religion", readonly=True)
    section = fields.Char(related="employee_id.section", readonly=True)
    sponsor = fields.Char(related="employee_id.sponsor", readonly=True)
    employee_name_arabic = fields.Char(related="employee_id.employee_name_arabic", readonly=True)
    previous_employee_code = fields.Char(related="employee_id.previous_employee_code", readonly=True)
    attendance_report_range = fields.Selection(related="employee_id.attendance_report_range", readonly=True)
    need_to_log_timesheet = fields.Boolean(related="employee_id.need_to_log_timesheet", readonly=True)
    allow_overtime = fields.Boolean(related="employee_id.allow_overtime", readonly=True)

    emp_code_old = fields.Char(related="employee_id.emp_code_old", readonly=True)
    first_name_passport = fields.Char(related="employee_id.first_name_passport", readonly=True)
    middle_name_passport = fields.Char(related="employee_id.middle_name_passport", readonly=True)
    last_name_passport = fields.Char(related="employee_id.last_name_passport", readonly=True)
    date_of_joining = fields.Date(related="employee_id.date_of_joining", readonly=True)
    section = fields.Char(related="employee_id.section", readonly=True)
    civil_id = fields.Char(related="employee_id.civil_id", readonly=True)
    civil_expiry = fields.Date(related="employee_id.civil_expiry", readonly=True)
    passport_expiry_date = fields.Date(related="employee_id.passport_expiry_date", readonly=True)
    salary_pay_mode = fields.Char(related="employee_id.salary_pay_mode", readonly=True)
    bank_iban = fields.Char(related="employee_id.bank_iban", readonly=True)
    work_permit_position = fields.Char(related="employee_id.work_permit_position", readonly=True)
    work_permit_salary = fields.Char(related="employee_id.work_permit_salary", readonly=True)
    personal_contact_no = fields.Char(related="employee_id.personal_contact_no", readonly=True)
    personal_email_id = fields.Char(related="employee_id.personal_email_id", readonly=True)



class HREmployee(models.Model):

    _inherit = 'hr.employee'

    emp_code = fields.Char(string="Employee ID")
    grade_id = fields.Many2one("hr.employee.grade", string="Grade")
    exit_date = fields.Date(string="Exit Date", help="Last working day of the employee")
    probation_period = fields.Integer(string="Probation Period in Days", tracking=True)
    notice_period = fields.Integer(string="Notice Period in Days", tracking=True)
    opt_for_attendance_mail = fields.Boolean(string="Opt for Attendance Report Mail")
    state = fields.Selection(
        [
            ("joined", "Joined"),
            ("probation", "On Probation"),
            ("employment", "Employment"),
            ("notice_period", "Notice Period"),
            ("resigned", "Resigned"),
            ("terminated", "Terminated")
        ], string="Status", default="joined", required=True
    )

    religion = fields.Selection(
        [
            ("Christianity","Christianity"),
            ("Islam","Islam"),
            ("Irreligion","Irreligion"),
            ("Hinduism","Hinduism"),
            ("Buddhism","Buddhism"),
            ("Folk Religions","Folk Religions"),
            ("Sikhism","Sikhism"),
            ("Judaism","Judaism")
        ], string="Religion"
    )
    section = fields.Char(string="Section")
    sponsor = fields.Char(string="Sponsor")
    sponsor_company_id = fields.Many2one('res.company', string="Sponsor Company")
    employee_name_arabic = fields.Char(string="Employee Name in Arabic")
    previous_employee_code = fields.Char(string="Previous Employee Code")

    employee_dependency_ids = fields.One2many("hr.employee.dependent", "employee_id")
    employee_emergency_ids = fields.One2many("hr.employee.emergency", "employee_id")
    employee_qualification_ids = fields.One2many("hr.employee.qualification", "employee_id")

    attendance_report_range = fields.Selection(
        [
            ('this_month', 'This Month'),
            ('last_month', 'Last Month')
        ], default='this_month', string='Report Range'
    )
    need_to_log_timesheet = fields.Boolean(string="Need to Log Timesheet", default=True)
    allow_overtime = fields.Boolean(string="Allow Overtime")

    emp_code_old = fields.Char(string="Old Employee Code")
    first_name_passport = fields.Char(string="First Name - Passport")
    middle_name_passport = fields.Char(string="Middle Name - Passport")
    last_name_passport = fields.Char(string="Last Name - Passport")
    date_of_joining = fields.Date(string="Date of Joining")
    service_period = fields.Float(string="Service Period")
    section = fields.Char(string="Section")
    civil_id = fields.Char(string="Civil ID")
    civil_expiry = fields.Date(string="Civil ID Expiry")
    passport_expiry_date = fields.Date(string="Passport Expiry Date")
    salary_pay_mode = fields.Char(string="Salary Pay Mode")
    employee_bank_name = fields.Char(string="Employee Bank Name")
    bank_iban = fields.Char(string="Bank IBAN")
    work_permit_position = fields.Char(string="Work Permit Position")
    work_permit_salary = fields.Char(string="Work Permit Salary")
    personal_contact_no = fields.Char(string="Personal Contact Number")
    personal_email_id = fields.Char(string="Personal Email ID")
    age = fields.Float(string="Age")

    wage = fields.Float(string="Basic", compute='_compute_employee_salary')
    hra = fields.Float(string='HRA', help="House rent allowance.", compute='_compute_employee_salary')
    travel_allowance = fields.Float(string="Travel Allowance", help="Travel allowance",
                                    compute='_compute_employee_salary')
    da = fields.Float(string="DA", help="Dearness allowance", compute='_compute_employee_salary')
    meal_allowance = fields.Float(string="Meal Allowance", help="Meal allowance", compute='_compute_employee_salary')
    medical_allowance = fields.Float(string="Medical Allowance", help="Medical allowance",
                                     compute='_compute_employee_salary')
    other_allowance = fields.Float(string="Other Allowance", help="Other allowances",
                                   compute='_compute_employee_salary')
    employee_contribution_perc = fields.Float(string="Employee Contribution %", compute='_compute_employee_salary')
    employer_contribution_perc = fields.Float(string="Employer Contribution %", compute='_compute_employee_salary')
    employee_leave_details_ids = fields.Many2many('hr.leave', string="Employee Leave Information")

    uan = fields.Integer(string="UAN Number")
    esi = fields.Integer(string="ESI Number")
    wwf = fields.Integer(string="WWF Number")
    # address
    permanent_address = fields.Char('Street')
    p_street2 = fields.Char('Street2')
    p_zip = fields.Char('Zip')
    p_city = fields.Char('City')
    p_state_id = fields.Many2one("res.country.state", string='State')
    p_country_id = fields.Many2one('res.country', string='Country')
    # address
    present_address = fields.Char('Street')
    street2 = fields.Char('Street2')
    zip = fields.Char('Zip')
    city = fields.Char('City')
    state_id = fields.Many2one("res.country.state", string='State')
    country_id = fields.Many2one('res.country', string='Country')

    aadhar_number = fields.Char(string="Aadhar Number")
    pan = fields.Char(string="PAN Number")
    father_name = fields.Char(string="Father Name")
    mother_name = fields.Char(string="Mother Name")

    ifsc = fields.Char(string="IFSC Code")
    last_working_day = fields.Date(string="Date of Last Working Day")
    date_of_resignation = fields.Date(string="Date of Resignation")
    date_of_promotions = fields.Date(string="Date of Promotions")
    date_of_increments = fields.Date(string="Date of Increments")
    date_of_probation = fields.Date(string="Date of Probation Confirmation")
    employee_bank_name = fields.Char(string="Employee Bank Name")

    misc_allowance = fields.Monetary(string="Misc.Allowance", compute='_compute_employee_salary')
    variable_inc = fields.Monetary(string="Variable Inc", compute='_compute_employee_salary')
    arrears = fields.Monetary(string="Arrears", compute='_compute_employee_salary')
    other_earnings = fields.Monetary(string="Other Earnings", compute='_compute_employee_salary')
    incentive = fields.Monetary(string="Incentive", compute='_compute_employee_salary')
    gmi_release = fields.Monetary(string="GMI Release", compute='_compute_employee_salary')

    enmfi = fields.Boolean(string="Emp Non Mandatory Fields Hide", help="Non mandatory fields hide for indian company.", compute='_compute_company')
    kuwait_company = fields.Boolean(string="Kuwait Company", help="Non mandatory fields hide for Kuwait company.", compute='_compute_company')
    visa_no = fields.Char('Visa Number (Article)', groups="hr.group_hr_user", tracking=True)


    def _compute_company(self):
        if self.company_id:
            for rec in self:
                rec.enmfi = rec.company_id.enmfi
                rec.kuwait_company = rec.company_id.kuwait_company


    def _compute_employee_salary(self):
        for rec in self:
            rec.wage = rec.contract_id.wage
            rec.hra = rec.contract_id.hra
            rec.travel_allowance = rec.contract_id.travel_allowance
            rec.da = rec.contract_id.da
            rec.meal_allowance = rec.contract_id.meal_allowance
            rec.medical_allowance = rec.contract_id.medical_allowance
            rec.other_allowance = rec.contract_id.other_allowance
            rec.employee_contribution_perc = rec.contract_id.employee_contribution_perc
            rec.employer_contribution_perc = rec.contract_id.employer_contribution_perc
            rec.misc_allowance = rec.contract_id.misc_allowance
            rec.variable_inc = rec.contract_id.variable_inc
            rec.arrears = rec.contract_id.arrears
            rec.other_earnings = rec.contract_id.other_earnings
            rec.incentive = rec.contract_id.incentive
            rec.gmi_release = rec.contract_id.gmi_release

    @api.model
    def create(self, values):
        if not values.get('emp_code'):
            values['emp_code'] = self.env[
                'ir.sequence'].next_by_code('jic.employee.sequence')
        return super(HREmployee, self).create(values)

    @api.model
    def action_get(self):
        return self.env['ir.actions.act_window']._for_xml_id('jic_hr_base.open_view_employee_list_my_inherit')

    @api.model
    def emp_id_get(self):
        emp_id = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        return emp_id.id

    @api.onchange('civil_expiry')
    def onchange_civil_expiry_date(self):
        for rec in self:
            if rec.civil_expiry:
                rec.visa_expire = rec.civil_expiry
