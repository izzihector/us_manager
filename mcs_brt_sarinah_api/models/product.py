# -*- coding: utf-8 -*-
# DEVELOPMENT BY : BRATA BAYU SIAHALA, S.KOM

from odoo import fields, models, api, _ ,tools
from odoo.exceptions import UserError
from odoo import SUPERUSER_ID
import psycopg2
import itertools
from odoo.exceptions import ValidationError, except_orm


class ProductBrand(models.Model):
    _inherit = 'product.template'

    is_populer = fields.Boolean(string="Product Populer ?")