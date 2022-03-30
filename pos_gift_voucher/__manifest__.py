# -*- coding: utf-8 -*-
{
    'name': 'POS Gift Coupon Management',
    'version': '13.0.0',
    'category': 'Point Of Sale',
    'author': 'Pragmatic TechSoft Pvt Ltd.',
    'website': 'http://www.pragmatic.com',
    'summary': 'Odoo POS Gift Coupon odoo pos odoo point of sale pos gift voucher point of sale gift voucher',
    'description': """
This module shows the basic processes functionality for Gift Voucher
====================================================================
<keywords>
odoo pos
odoo point of sale 
pos gift voucher
point of sale gift voucher
    """,
    'depends': ['base', 'point_of_sale', 'bs_sarinah_product'],
    'data': [
        'security/ir.model.access.csv',
        'views/template.xml',
        'views/gift_voucher.xml',
    ],
    'qweb': [
        'static/src/xml/pos.xml',
        'static/src/xml/voucher.xml',
    ],
    'images': ['images/Animated-pos-gift.gif'],
    'live_test_url': 'http://www.pragtech.co.in/company/proposal-form.html?id=103&name=Odoo-POS-Gift-Management',
    'license': 'OPL-1',
    'price': 150,
    'currency': 'EUR',
    'auto_install': False,
    'installable': True,
}
