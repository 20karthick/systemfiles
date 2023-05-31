# -*- coding: utf-8 -*-

{
    'name': 'Odoo15 Payroll Extension',
    'category': 'JIC Payroll extension',
    'version': '15.0.1.0.0',
    'author': 'JIC',
    'company': 'JIC IT',
    'maintainer': 'JIC',
    'website': '',
    'summary': 'Payroll extension for JIC',
    'images': [],
    'description': "Odoo 15 Payroll extension",
    'depends': [
        'hr_payroll_community', 'jic_hr_base', 'jic_hr_attendance_report', 'hr_holidays'
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/hr_payroll_security.xml',
        'data/salary_rule.xml',
        'data/payroll_input_category.xml',
        "views/sequence.xml",
        "views/email_templates.xml",
        "wizard/data_import_wizard.xml",
        "wizard/payslip_email.xml",
        "wizard/hr_payroll_diagnosis.xml",
        "wizard/bulk_extra_input_requests_view.xml",
        "views/hr_department.xml",
        "views/hr_employee_extra_input.xml",
        "views/hr_overtime.xml",
        "views/hr_contract.xml",
        "views/hr_payslip.xml",
        "views/hr_salary_rule.xml",
        "views/hr_leave_type.xml",
        "views/payslip_template_inherit.xml"
    ],
    'demo': [],
    'license': 'AGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
