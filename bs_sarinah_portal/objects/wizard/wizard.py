# -*- coding: utf-8 -*-
# Copyright 2020 Bumiswa

"""
TECHNICAL GUIDE
1. Name this python file based on the model name.
2. This file may contains two or more models.
3. The first model is main model (i.e. sale.order).
4. The next model should be related to main model & use its name as the prefix (i.e. sale.order.line, sale.order.promo).
5. You may remove this technical guide after you've done creating the model.
"""

from odoo import api, fields, models