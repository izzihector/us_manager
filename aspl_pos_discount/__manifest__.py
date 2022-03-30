# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################
{
    'name': 'POS Custom Discount',
    'category': 'Point of Sale',
    'summary': 'This module allows the seller to apply discount on single product as well as complete order in POS session.',
    'description': """
This module allows the seller to apply discount on 
single product as well as complete order in POS session.
""",
    'author': 'Acespritech Solutions Pvt. Ltd.',
    'website': 'http://www.acespritech.com',
    'price': 30.00, 
    'currency': 'EUR',
    'version': '1.0.1',
    'depends': ['base', 'point_of_sale'],
    'images': ['static/description/main_screenshot.png'],
    "data": [
         'views/aspl_pos_discounts_view.xml',
         'views/template.xml',
         'security/ir.model.access.csv',
         'data/aspl_pos_discount_demo.xml',
    ],
    'qweb': ['static/src/xml/pos.xml'],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
