# -*- coding: utf-8 -*-
{
    'name': "Inherit fully payment invoice",

    'summary': """
        Script yang inherit ke modul accounting.""",

    'description': """
        >.
    """,

    'author': "GSF - MCS",
    'website': "http://www.matrica.co.id",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'account',
        ],

    # always loaded
    'data': [
        'views/view.xml',
    ],
    # only loaded in demonstration mode
    # 'demo': [
    #     'demo/demo.xml',
    # ],
}
