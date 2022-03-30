# -*- coding: utf-8 -*-
##############################################################################
#
#    TL Technology
#    Copyright (C) 2019 ­TODAY TL Technology (<https://www.posodoo.com>).
#    Odoo Proprietary License v1.0 along with this program.
#
##############################################################################
{
    'name': 'POS Big Datas',
    'version': '8.8.0.2',
    'category': 'Point of Sale',
    'sequence': 0,
    'author': 'TL Technology',
    'website': 'http://posodoo.com',
    'price': '75',
    'description': 'Supported loading: \n'
                   '- Products big datas\n'
                   '- Customer big datas\n'
                   'TO POS Session',
    "currency": 'EUR',
    'depends': ['point_of_sale', 'bus', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'import/template.xml',
        'data/schedule.xml',
        'view/pos_config.xml',
        'view/pos_call_log.xml',
        'view/pos_cache_database.xml',
    ],
    'qweb': ['static/src/xml/*.xml'],
    'application': True,
    'images': ['static/description/icon.png'],
    'support': 'thanhchatvn@gmail.com',
    "license": "OPL-1",
}
