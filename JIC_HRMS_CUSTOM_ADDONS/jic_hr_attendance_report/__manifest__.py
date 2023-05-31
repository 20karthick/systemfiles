# -*- coding: utf-8 -*-

{
    'name': 'Odoo15 Attendance Report',
    'category': 'JIC Attendance report',
    'version': '15.0.1.0.0',
    'author': 'JIC',
    'company': 'JIC IT',
    'maintainer': 'JIC',
    'website': '',
    'summary': 'Attendance report',
    'images': [],
    'description': "Odoo 15 Attendance Report",
    'depends': [
        'hr_attendance', 'jic_hr_base'
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'wizard/attendance_report_view.xml',
        "views/sequence.xml",
        "views/email_template.xml",
        "views/cron_job.xml",
        'views/xlsx_templates.xml',
        'views/regularization_category.xml',
        'views/hr_attendance_regularization_view.xml',
        'views/allowed_ip.xml',
        'views/hr_employee.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'jic_hr_attendance_report/static/src/js/attendance_restrict_by_ip.js',
        ],
    },
    'demo': [],
    'license': 'AGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
