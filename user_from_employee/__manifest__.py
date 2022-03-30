# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    # App information

    'name': 'Create a user from an employee',
    'category': 'Human Resources',
    'version': '12.0.1.1',
    'summary': """
                This module allows you to create a user from an employee.
              """,
    'license': 'AGPL-3',

    # Dependencies
    'depends': ['hr'],

    # Views
    'data': [
        'views/res_users_views.xml',
        'views/hr_views.xml',
        'views/hr_employee_create_user_wiz.xml',
    ],

    # Author

    'author': 'Mihajarilala Rakotondriatsara',
    'maintainer': 'Mihajarilala Rakotondriatsara',
    'support': 'mihajarilala@gmail.com',

    # Odoo Store Specific

    'images': ['static/description/create_user_from_employee_screenshoot.png'],

    # Technical

    'installable': True,
    'application': True,
    'auto_install': False,

}
