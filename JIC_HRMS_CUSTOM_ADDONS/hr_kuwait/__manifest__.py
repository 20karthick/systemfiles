# -*- coding: utf-8 -*-

{
    'name': 'Odoo 15 Hr base for Kuwait Only',
    'version': '15.0.1.0.0',
    'category': 'General',
    'description': 'Base Module for Kuwait HR ',
    'summary': 'Essential module for work with JIC Projects',
    'sequence': '1',
    'author': 'JIC IT Solutions',
    'license': 'LGPL-3',
    'company': 'JIC IT Solutions',
    'maintainer': 'JIC',
    'support': 'jic@gmail.com',
    'website': 'https://www.jic.com',
    'depends': ['jic_hr_base'],
    'live_test_url': '',
    'data': [
        "data/hr_leave_type.xml",
        "data/salary_rule.xml",
    ],
    'pre_init_hook': '',
    'installable': True,
    'application': False,
    'auto_install': False,
    'images': [],
}
