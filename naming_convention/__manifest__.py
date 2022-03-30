# -*- coding: utf-8 -*-
{
    'name': "Naming Convention",

    'summary': """
        1. Menambahkan naming convention pada master product dan configuration di Inventory.
        2. Menambahkan naming convention pada catalog product dan reporting pivot view di Sales.""",

    'description': """
        >.
    """,

    'author': "WGP - MCS",
    'website': "http://www.matrica.co.id",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','stock', 'sale'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        # 'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
}