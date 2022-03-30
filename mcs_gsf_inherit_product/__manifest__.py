# -*- coding: utf-8 -*-
{
    'name': "MCS | GSF Inherit Product",

    'summary': """Product - MCS""",

    'description': """
        Module Inherit Product
    """,

    'author': "Ghiyats Syah Fitrah",
    'website': "http://www.matrica.co.id",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'GSF',
    'version': '13.0',

    # any module necessary for this one to work correctly
    'depends': ['stock'],
    # 'images': ['matrica.jpg'],
    # always loaded
    'data': [
        'view/views.xml',

        # 'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
}
