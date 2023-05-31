# -*- coding: utf-8 -*-

{
    'name': 'Odoo15 Entry Exit Extension',
    'category': 'JIC Entry/Exit extension',
    'version': '15.0.1.0.0',
    'author': 'JIC',
    'company': 'JIC IT',
    'maintainer': 'JIC',
    'website': '',
    'summary': 'Entry / Exit extension for JIC',
    'images': [],
    'description': "Odoo 15 Entry Exit extension",
    'depends': [
        'hr_contract', 'jic_hr_base', 'hr_recruitment', 'hr_skills'
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/hr_separation_security.xml',
        'data/hr_checklist_type.xml',
        "views/sequence.xml",
        "views/email_templates.xml",
        "views/hr_employee_view.xml",
        "views/hr_employee_public.xml",
        "views/hr_contract_view.xml",
        "views/hr_skills_view.xml",
        "views/hr_employee_separation.xml",
        "views/hr_employee_checklist.xml",
        "views/hr_recruitment_view.xml",
        "views/hr_employee_offer_letter.xml"
    ],
    'demo': [],
    'license': 'AGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
