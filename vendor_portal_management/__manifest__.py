# -*- coding: utf-8 -*-
{
    "name": "Vendor Products Portal",
    "version": "13.0.1.0.1",
    "category": "Purchases",
    "author": "faOtools",
    "website": "https://faotools.com/apps/13.0/vendor-products-portal-447",
    "license": "Other proprietary",
    "application": True,
    "installable": True,
    "auto_install": False,
    "depends": [
        "vendor_product_management",
        "website"
    ],
    "data": [
        "data/data.xml",
        "security/ir.model.access.csv",
        "security/security.xml",
        "views/view.xml",
        "views/res_config_settings.xml",
        "views/core_templates.xml",
        "views/vendor_product_template.xml",
        "views/vendor_location_template.xml"
    ],
    "qweb": [
        "static/src/xml/*.xml"
    ],
    "js": [
        
    ],
    "demo": [
        
    ],
    "external_dependencies": {},
    "summary": "The tool to motivate vendors to prepare product catalogue in your Odoo",
    "description": """
For the full details look at static/description/index.html

* Features * 
- Vendor products catalog in portal
- Vendor stocks control without effort
- Supplier prices management and self-management
- Comfortable importing of vendor product data

* Extra Notes *
- How vendor stocks work
- How to import vendor products and stocks
- How to import vendor product and prices


#odootools_proprietary

    """,
    "images": [
        "static/description/main.png"
    ],
    "price": "85.0",
    "currency": "EUR",
    "live_test_url": "https://faotools.com/my/tickets/newticket?&url_app_id=101&ticket_version=13.0&url_type_id=3",
}