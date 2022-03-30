# -*- coding: utf-8 -*-
{
    "name": "Vendor Product Management",
    "version": "13.0.1.0.2",
    "category": "Purchases",
    "author": "faOtools",
    "website": "https://faotools.com/apps/13.0/vendor-product-management-448",
    "license": "Other proprietary",
    "application": True,
    "installable": True,
    "auto_install": False,
    "depends": [
        "purchase",
        "base_import"
    ],
    "data": [
        "data/data.xml",
        "security/ir.model.access.csv",
        "views/res_config_settings.xml",
        "views/vendor_quant.xml",
        "views/vendor_location.xml",
        "views/product_supplierinfo.xml",
        "views/vendor_product.xml",
        "views/product_template.xml",
        "views/product_product.xml",
        "views/res_partner.xml",
        "wizard/vendor_import_result.xml",
        "wizard/vendor_product_import.xml",
        "wizard/vendor_stock_import.xml",
        "views/menu.xml"
    ],
    "qweb": [
        
    ],
    "js": [
        
    ],
    "demo": [
        
    ],
    "external_dependencies": {},
    "summary": "The tool to administrate vendor data about products, prices and available stocks",
    "description": """
For the full details look at static/description/index.html
- Involve vendors themselves in product management using the tool &lt;a href='https://apps.odoo.com/apps/modules/13.0/vendor_portal_management/'&gt;Vendor Products Portal&lt;/a&gt;

* Features * 
- Vendor products catalog
- Vendor stocks control
- Supplier prices management
- Comfortable importing of vendor product data

* Extra Notes *
- How vendor stocks work
- How to import vendor product and prices
- How to import vendor products and stocks


#odootools_proprietary

    """,
    "images": [
        "static/description/main.png"
    ],
    "price": "73.0",
    "currency": "EUR",
    "post_init_hook": "post_init_hook",
    "live_test_url": "https://faotools.com/my/tickets/newticket?&url_app_id=100&ticket_version=13.0&url_type_id=3",
}