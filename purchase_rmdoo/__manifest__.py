# -*- coding: utf-8 -*-
{
    'name': "Sarinah Purchase Dev",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Purchase Sarinah Development
    """,

    'author': "Bumiswa",
    'website': "https://rmdoo.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Purchase',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base_rmdoo',
        'product',
        'purchase_discount',
        'purchase_requisition',
        'stock_landed_costs',
        'stock_dropshipping',
        'recurring_purchase',
    ],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/functions.xml',
        'views/views.xml',
        'views/templates.xml',
        'views/inquiry_report_view.xml',
        'views/replenish_request_view.xml',
        'data/ir_sequence_data.xml',
        'reports/purchase_replenish_report.xml',
        'reports/purchase_outstanding_report.xml',
        'reports/purchase_outstanding_rmdoo_report.xml',
        'reports/purchase_totalbyvendors.xml',
        'reports/purchase_order_report.xml',
        'reports/purchase_order_report_template.xml',
        'reports/purchase_agreement.xml',
        'reports/purchase_request.xml',
        'reports/purchase_history.xml',
        'wizard/po_split.xml',
        'wizard/pr_vendor_fill.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
