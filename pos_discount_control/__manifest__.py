# -*- coding: utf-8 -*-
{
    'name': 'POS Discount Control',
    'version': '1.0',
    'category': 'Point of Sale',
    "license": "OPL-1",
    'price': 9,
    'currency': 'EUR',
    'description': """
        Restrict discount modification to managers
    """,
    'author': 'Felix',
    'depends': [
        'point_of_sale',
        'pos_hr'
    ],
    'data': [
        "views/pos_config_view.xml",
        "views/pos_view.xml",
    ],

    'test': [],
    'demo': [],
    'qweb': [

    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'active': True,
    'application': False,
}
