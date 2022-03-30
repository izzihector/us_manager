# -*- coding: utf-8 -*-
# Copyright 2019 Bumiswa
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
{
    "name": """Sarinah Vendor Portal""",
    "summary": """Custom vendor portal for sarinah.""",
    "category": "Website",
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
        'uom',
        'sale',
        'pos_sale',
        'l10n_id_efaktur',
        # third party addons
        'branch',
        'vendor_portal_management',
        'bi_product_brand',
        'mcs_product_naming_brand_category',
        'aspl_pos_discount',
        'mcs_aspl_pos_discount_auto',
        'report_xlsx',
        # developed addons
        'bs_sarinah_department',
        'bs_consignment_bills',
    ],
    "data": [
        # group
        'security/res_groups.xml',

        # data

        # global action
        'views/action/action.xml',

        # view
        'views/common/res_partner.xml',
        'views/common/vendor_product_attribute.xml',
        'views/common/vendor_product_variant.xml',
        'views/common/vendor_product.xml',
        'views/common/vendor_location.xml',
        'views/common/vendor_quant.xml',
        'views/common/res_branch.xml',
        'views/common/product_supplierinfo.xml',
        # 'views/common/res_config_settings.xml',
        'views/common/uom_category.xml',
        'views/common/vendor_stock_picking.xml',
        'views/common/product_category.xml',
        'views/common/product_brand.xml',
        'views/common/product_pricelist.xml',
        'views/common/product_product.xml',

        'views/template/vendor_location.xml',
        'views/template/vendor_product.xml',
        'views/template/vendor_product_variant.xml',
        'views/template/vendor_home.xml',
        'views/template/vendor_low_stock.xml',
        'views/template/vendor_stock_picking.xml',
        'views/template/vendor_sales_report.xml',

        # wizard
        'views/wizard/wizard_ppbk_report.xml',
        'views/wizard/wizard_vendor_stock_picking.xml',

        # report paperformat
        # 'data/report_paperformat.xml',

        # report template
        'views/report/vendor_stock_picking.xml',
        'views/report/web_ppbk_report.xml',

        # report action
        'views/action/action_report.xml',

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
        'security/ir_rule.xml',

        # data
        'data/ir_sequence.xml',
    ],
    "demo": [
        # 'demo/demo.xml',
    ],
    "qweb": [
        "static/src/xml/vendor_portal.xml",
        "static/src/xml/ppbk_report.xml",
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
# noinspection PyUnresolvedReferences,SpellCheckingInspection
