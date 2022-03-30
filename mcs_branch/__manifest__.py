# -*- coding: utf-8 -*-
{
    'name': "MCS | Branch",

    'summary': """
       Module Branch (Bisnis Unit)""",

    'description': """
        Long description of module's purpose
    """,

    'author': "MCS | Brata Bayu",
    'website': "http://www.matrica.co.id",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Base',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        'security/branch_security.xml',
        'security/ir.model.access.csv',
        'views/branch.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
