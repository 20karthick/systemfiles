# -*- coding: utf-8 -*-

{
    'name': 'Odoo 15 Base Module for JIC HR',
    'version': '15.0.1.0.0',
    'category': 'General',
    'description': 'Base Module for JIC HR projects ',
    'summary': 'Essential module for work with JIC HR Projects',
    'sequence': '1',
    'author': 'JIC IT Solutions',
    'license': 'LGPL-3',
    'company': 'JIC IT Solutions',
    'maintainer': 'JIC',
    'support': 'jic@gmail.com',
    'website': 'https://www.jic.com',
    'depends': ['jic_base', 'hr', 'hr_attendance', 'hr_holidays', 'project', 'hr_timesheet'],
    'live_test_url': '',
    'data': [
        'security/ir.model.access.csv',
        "views/jic_project_timesheet.xml",
        "views/jic_project_task.xml",
        "views/jic_employee_sequence_view.xml",
        "views/hr_employee_qualification_view.xml",
        "views/jic_hr_employee.xml",
        "views/res_company_view.xml",
        "views/hr_employee_grade.xml",
        "views/hr_department.xml"
    ],
    'pre_init_hook': '',
    'installable': True,
    'application': False,
    'auto_install': False,
    'images': [],
}
