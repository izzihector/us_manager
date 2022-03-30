{
    "name": "Mobile UI for POS",
    "category": "Point Of Sale",
    "author": "StyleCre, "
              "Pablo Carrio Garcia",
    "version": "13.0.1.1.2",
    "website": "https://stylecre.es/odoo",
    "summary": "Responsive POS theme, POS Mobile improved UI. For using as a Mobile POS. Collapsible interface. Tablet POS UI.",
    "price": 90.0,
    "currency": "EUR",
    "support": "odoo@stylecre.es",
    "license": "OPL-1",
    'images': ['static/description/main_screenshot.jpg','static/description/screenshot_1.jpg','static/description/screenshot_2.jpg','static/description/screenshot_3.jpg'],
    "depends": [
        "point_of_sale",
    ],
    "data": [
        "views/pos_templates.xml",
    ],
    "qweb": [
        "static/src/xml/mobile_pos.xml",
    ],
    "installable": True
}
