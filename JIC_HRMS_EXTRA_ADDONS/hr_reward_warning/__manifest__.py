
{
    'name': 'Open HRMS Official Announcements',
    'version': '15.0.1.1.0',
    'summary': """Managing Official Announcements""",
    'description': 'This module helps you to manage hr official announcements',
    'live_test_url': 'https://youtu.be/VPh1A9-jM5Q',
    'category': 'Generic Modules/Human Resources',
    'author': 'Cybrosys Techno solutions,Open HRMS',
    'company': 'Cybrosys Techno Solutions',
    'website': "https://www.openhrms.com",
    'depends': ['base', 'hr', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'security/reward_security.xml',
        'views/hr_announcement_view.xml',
        'views/email_template.xml'
    ],
    'demo': ['data/demo_data.xml'],
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
