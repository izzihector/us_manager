# Part of Softhealer Technologies.
{
    "name": "Point Of Sale Logo",
    "author": "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "support": "support@softhealer.com",
    "category": "point of sale",
    "summary": "POS Receipt Company Logo, Point Of Sale Custom Logo App, Set POS Receipt Logo Module, company logo In POS, POS Receipt Logo, Point Of Sale Receipt Logo Odoo",
    "description": """Currently, in the odoo, you have no option to set the company logo & custom logo in the POS receipt. This module helps to add the company logo and custom logo in the "Point Of Sale Receipt". You can set a logo on every receipt of the point of sale. Point Of Sale Receipt Logo Odoo,Company Logo In POS Receipt, Point Of Sale Custom Logo, Set POS Receipt Logo Module, Print company logo In POS, POS Receipt Logo, Point Of Sale Receipt Logo Odoo, POS Receipt Company Logo, Point Of Sale Custom Logo App, Set POS Receipt Logo Module, company logo In POS, POS Receipt Logo, Point Of Sale Receipt Logo Odoo.""",
    "version": "13.0.2",
    "depends": ["base", "web", "point_of_sale"],
    "application": True,
    "data": [
        'views/pos_config_settings.xml',
        'views/assets.xml',
    ],
    "images": ["static/description/background.png", ],
    "live_test_url": "https://youtu.be/negkR9CwIn8",
    "qweb": ["static/src/xml/pos.xml"],
    "auto_install": False,
    "installable": True,
    "price": "30",
    "currency": "EUR"
}
