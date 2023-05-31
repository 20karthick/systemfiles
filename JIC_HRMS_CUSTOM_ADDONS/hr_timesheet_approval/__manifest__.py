# -*- coding: utf-8 -*-

{
    'name': 'Odoo15 Timesheet Approval',
    'category': 'Generic Modules/Human Resources',
    'version': '15.0.1.0.0',
    'author': 'Pycus',
    'company': 'Pycus Tech',
    'maintainer': 'Pycus',
    'website': '',
    'summary': 'Manage your timesheet approvals',
    'images': ['static/description/icon_timesheet.png'],
    'description': "Odoo 15 Timesheet approval",
    'depends': [
        'hr_timesheet','project','analytic', 'web_timeline'
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/timesheet_approval_security.xml',
        'wizard/timesheet_approval_wizard_view.xml',
        'views/hr_timesheet_entry.xml',
    ],
    'demo': [],
    'license': 'AGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
