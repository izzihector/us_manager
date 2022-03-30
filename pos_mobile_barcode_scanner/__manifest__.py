# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    "name": "POS Mobile BarCode Scanner",
    "category": "Point Of Sale",
    "author": "StyleCre, "
              "Pablo Carrio Garcia",
    "website": "https://stylecre.es/odoo",
    "summary": "BarCode Scanner for mobile and desktop devices. Camera barcode scanner.",
    "version": "1.0.2",
    "license": "LGPL-3",
    "price": 55.0,
    "currency": "EUR",
    "support": "odoo@stylecre.es",
    "images": ["static/description/main_screenshot.jpg","static/description/screenshot_1.jpg","static/description/screenshot_2.jpg","static/description/screenshot_3.jpg","static/description/screenshot_4.jpg","static/description/screenshot_5.jpg"],
    "depends": [
        "point_of_sale"
    ],
    "data": [
        "views/pos_templates.xml",
        "views/pos_views.xml",
    ],
    "qweb": [
        "static/src/xml/mobile_pos.xml",
    ],
    "installable": True
}
