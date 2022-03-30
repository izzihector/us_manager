# -*- coding: utf-8 -*-
{
    'name': "mcs_product_naming_brand_category",

    'summary': """
        Auto naming product based on its brand and 2 last categories""",

    'description': """
        Long description of module's purpose
    """,

    'author': "MCS - LLHa",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'bi_product_brand'],

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
