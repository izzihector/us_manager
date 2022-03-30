# -*- coding: utf-8 -*-
# Copyright 2019 Bumiswa
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
# noinspection PyUnresolvedReferences,SpellCheckingInspection
{
    "name": """Sarinah Department Access""",
    "summary": """Custom access based on department""",
    "category": "Extra Rights",
    "version": "13.0.0.1.0",
    "development_status": "Alpha",  # Options: Alpha|Beta|Production/Stable|Mature
    "auto_install": False,
    "installable": True,
    "application": False,
    "author": "Bumiswa",
    "support": "support@rmdoo.com",
    # "website": "https://rmdoo.com",
    "license": "OPL-1",
    "images": [
        'images/main_screenshot.png'
    ],

    # "price": 10.00,
    # "currency": "USD",

    "depends": [
        # odoo addons
        'base',
        'hr',
        'purchase',
        'sale',
        'stock',
        'account',
        'point_of_sale',
        'account_reports',
        # third party addons
        'branch',
        'branch_accounting_report',
        'purchase_rmdoo',

        # developed addons
    ],
    "data": [
        # group
        'security/res_groups.xml',

        # data

        # global action
        # 'views/action/action.xml',

        # view
        'views/common/account_journal.xml',
        'views/common/account_move.xml',
        'views/common/account_payment.xml',
        'views/common/crm_team.xml',
        'views/common/pos_config.xml',
        'views/common/pos_payment_method.xml',
        'views/common/product_pricelist.xml',
        'views/common/purchase_order.xml',
        'views/common/res_branch.xml',
        'views/common/sale_order.xml',
        'views/common/stock_location.xml',
        'views/common/stock_quant.xml',
        'views/common/stock_valuation_layer.xml',
        'views/common/stock_warehouse.xml',
        'views/common/stock_picking.xml',
        'views/common/search_template_view.xml',
        'views/common/res_config_settings.xml',
        'views/common/product_product.xml',
        'views/common/product_template.xml',
        'views/common/res_partner.xml',
        'views/common/hr_department.xml',

        # wizard

        # report paperformat
        # 'data/report_paperformat.xml',

        # report template
        # 'views/report/report_template_model_name.xml',

        # report action
        # 'views/action/action_report.xml',

        # assets
        'views/assets.xml',

        # onboarding action
        # 'views/action/action_onboarding.xml',

        # action menu
        'views/action/action_menu.xml',

        # action onboarding
        # 'views/action/action_onboarding.xml',

        # menu
        'views/menu.xml',

        # security
        'security/ir.model.access.csv',
        'security/ir.rule.csv',

        # data
    ],
    "demo": [
        # 'demo/demo.xml',
    ],
    "qweb": [
        # "static/src/xml/{QWEBFILE1}.xml",
    ],

    "post_load": None,
    # "pre_init_hook": "pre_init_hook",
    # "post_init_hook": "post_init_hook",
    "uninstall_hook": None,

    "external_dependencies": {"python": [], "bin": []},
    # "live_test_url": "",
    # "demo_title": "{MODULE_NAME}",
    # "demo_addons": [
    # ],
    # "demo_addons_hidden": [
    # ],
    # "demo_url": "DEMO-URL",
    # "demo_summary": "{SHORT_DESCRIPTION_OF_THE_MODULE}",
    # "demo_images": [
    #    "images/MAIN_IMAGE",
    # ]
}
