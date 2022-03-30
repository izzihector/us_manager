# -*- coding: utf-8 -*-
{
    'name': "MCS | Import Product Vendor",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Brata Bayu | Matrica Consulting Service",
    'website': "http://www.matrica.co.id",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    "depends": [
        "base",
        "vendor_product_management",
        "branch",
        "bs_sarinah_portal"
    ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/wizard_delete_product.xml',
        'views/wizard_import_produk.xml',
        # 'views/wizard_import_produk_bs.xml',
        'views/menu.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
