# See LICENSE file for full copyright and licensing details.

{
    "name": "POS Odoo Whatsapp Integration",
    "version": "13.0.1.0.0",
    "license": "LGPL-3",
    "summary": "POS Whatsapp Integration provides a feature to send message of the order done and receipt after payment is done.",
    "description": """
        POS Odoo Whatsapp Integration
        Odoo POS Whatsapp Integration
        POS whatsapp integration in odoo
        POS whatsapp integration with odoo
        Odoo POS Whatsapp Connector
        Odoo POS Whatsapp Integration App
        odoo pos whatsapp integration code
        odoo pos whatsapp integration github
        odoo pos whatsapp integration guide
        odoo pos whatsapp integration key
        odoo pos whatsapp integration list
        odoo pos whatsapp integration location
        odoo pos whatsapp integration online
        odoo pos whatsapp integration tutorial
        Odoo pos Whatsapp Integration
        POS Integration of odoo Whatsapp
        POS WhatsApp Odoo Integration
        Integrate Odoo with POS WhatsApp
        pos whatsapp connector in android
        pos whatsapp connector download
        pos whatsapp connector example
        pos whatsapp connector mobile
        pos whatsapp connector software
        odoo pos whatsapp connector android
        odoo pos whatsapp connector apk
        odoo pos whatsapp connector app
        odoo pos whatsapp connector download
        odoo pos whatsapp connector example
        odoo pos whatsapp connector ios
        Odoo pos Whatsapp Integration
        Odoo Sale Whatsapp Integration
        Odoo Account Whatsapp Integration
        Odoo HR Whatsapp Integration
        Odoo HR Payroll Whatsapp Integration
        Odoo Stock Whatsapp Integration
        Odoo POS Whatsapp
        pos Whatsapp Integration
        pos Whatsapp Connector
        pos Integration
        pos Connecter
        pos Whatsapp
        Odoo POS
        Whatsapp
        POS
    """,
    "author": "Serpent Consulting Services Pvt. Ltd.",
    "maintainer": "Serpent Consulting Services Pvt. Ltd.",
    "website": "http://www.serpentcs.com",
    "sequence": 5,
    "category": "Extra Tools",
    "depends": ["base_automation", "point_of_sale", "odoo_whatsapp_connector", "mail"],
    "data": [
        "report/report_view.xml",
        "report/pos_order_report_template.xml",
        "data/pos_data.xml",
        "views/pos_config.xml",
    ],
    "images": ["static/description/POS-WhatsApp-v14.gif"],
    "live_test_url": "https://www.youtube.com/watch?v=uU0JMxsUc30&t=80s",
    "post_init_hook": "_set_default_message_template",
    "installable": True,
    "price": 31,
    "currency": "EUR",
}
