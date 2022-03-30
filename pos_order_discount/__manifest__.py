# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################
{
  "name"                 :  "POS Order Discount",
  "summary"              :  """By default in Odoo Point of Sale, a discount is applied individually on every product instead of the total amount. Using this module seller can apply the discount on the total amount of the Sale Order.""",
  "category"             :  "Point of Sale",
  "version"              :  "1.1.0",
  "sequence"             :  1,
  "author"               :  "Webkul Software Pvt. Ltd.",
  "license"              :  "Other proprietary",
  "website"              :  "https://store.webkul.com/Odoo-POS-Order-Discount.html",
  "description"          :  """Odoo POS Order Discount
POS Order line discount
POS Orderline discount
Discount per product
POS Per product off
Odoo POS discount
Order discount
Fixed order line discount POS
Percentage discount odoo POS
Customer discount POS
Purchase discount 
Sales order discount""",
  "live_test_url"        :  "http://odoodemo.webkul.com/?module=pos_order_discount&custom_url=/pos/auto",
  "depends"              :  ['point_of_sale'],
  "data"                 :  [
                             'security/ir.model.access.csv',
                             'views/templates.xml',
                             'views/pos_discount_view.xml',
                            ],
  "demo"                 :  ['data/pos_order_discount_data.xml'],
  "qweb"                 :  [
                             'static/src/xml/discount.xml',
                             'static/src/xml/pos_discount.xml',
                            ],
  "images"               :  ['static/description/Banner.png'],
  "application"          :  True,
  "installable"          :  True,
  "auto_install"         :  False,
  "price"                :  35,
  "currency"             :  "USD",
  "pre_init_hook"        :  "pre_init_check",
}