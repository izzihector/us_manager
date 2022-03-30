# -*- coding: utf-8 -*-
{
    'name': "API Customer",

    'summary': """
        API Customer
        - Field date of birth
        - API get data customers
        - API get single data customer
        - API update data customer
    """,

    'description': """
        API Customer
        - Field date of birth
        - API get data customers
        - API get single data customer
        - API update data customer
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
