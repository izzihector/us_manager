# -*- coding: utf-8 -*-
{
    'name': "Sarinah Base",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Sarinah Base
    """,

    'author': "Bumiswa",
    'website': "https://rmdoo.com",

    # Categories can be used to filter modules in modules listing
    # for the full list
    'category': 'Base',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        #+ 'document',
        'contacts',
        'account',
        #+ 'account_parent',
        'stock',
        'stock_picking_batch',
        'l10n_generic_coa',
        'hr',
        'board',
        'product_expiry',
        'stock_landed_costs',
        'recurring',
        # 'recurring_account',
        'de_print_journal_entries',
        'prt_report_attachment_preview',
	#'report_attachment_preview',
        'inventory_dashboard',
        'stock_no_negative',
        'stock_forecast',
        'stock_warehouse_calendar',
        #'web_no_bubble',
        #'web_dialog_size',
        #'web_export_view',
        #'web_digital_sign',
        #'web_advanced_search',
        #'web_tree_resize_column',
        #'web_tree_many2one_clickable',
        #'web_listview_sticky_header',
        #'ks_dashboard_ninja',
        'dev_stock_inventory_report',
        # 'web_tree_dynamic_colored_field',
        # 'web_debranding',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/views.xml',
        'views/functions.xml',
        'views/templates.xml',
        'views/ir_sequence.xml',
        'views/inquiry_report_view.xml',
        'views/product_replenish_views.xml',
        'views/stock_move_close.xml',
        'reports/paperformat_rmdoo.xml',
        'reports/reports.xml',
        'reports/template_rmdoo.xml',
        'data/ir_sequence_data.xml',
        'data/ir_rule.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
    'qweb': [
        'static/src/xml/base.xml',
    ],
    'external_dependencies': {
        'python': [
            'num2words'
        ],
        "bin": []
    },
}
