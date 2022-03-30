# Part of Softhealer Technologies.
{
    "name": "Point Of Sale Order - Exchange & Return Barcode | Point Of Sale Product Exchange Barcode | Point Of Sale Product Return Barcode",
    "author": "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "support": "support@softhealer.com",
    "category": "Point of Sale",
    "summary": "POS Order Return,POS Order Exchange,Point Of Sale Order Return,Point Of Sale Order Exchange,POS Return Barcode,POS Exchange Barcode,POS Return Exchange,Point Of Sale Return,Point Of Sale Exchange,POS Product Exchange,POS Product Return Odoo",
    "license": "OPL-1",
    "description": "Currently, in every retail and most of the other business, there is one thing is common that is product return and exchange. But in odoo pos, there is no any feature product return and exchange. Don't worry about that, here is the solution. This module will help to manage your return and exchange products with stock quantities.",
    "version": "13.0.2",
    "depends": ["point_of_sale", "sh_pos_receipt_extend", "sh_pos_order_return_exchange"],
    "application": True,
    "data": [
        'views/sh_pos_order_return_exchange_barcode.xml',
    ],
    "qweb": [
        "static/src/xml/*.xml",
    ],
    "images": ["static/description/background.png", ],
    "auto_install": False,
    "installable": True,
    "price": 5,
    "currency": "EUR",
}
