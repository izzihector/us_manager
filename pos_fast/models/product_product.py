# -*- coding: utf-8 -*-
##############################################################################
#
#    TL Technology
#    Copyright (C) 2019 ­TODAY TL Technology (<https://www.posodoo.com>).
#    Odoo Proprietary License v1.0 along with this program.
#
##############################################################################
from odoo import api, fields, models, _

import logging

_logger = logging.getLogger(__name__)

class product_template(models.Model):

    _inherit = 'product.template'

    def write(self, vals):
        res = super(product_template, self).write(vals)
        for product_temp in self:
            products = self.env['product.product'].search([('product_tmpl_id', '=', product_temp.id)])
            for product in products:
                if product.sale_ok and product.available_in_pos:
                    self.env['pos.cache.database'].insert_data('product.product', product.id)
                if not product.available_in_pos or not product.active:
                    self.env['pos.cache.database'].remove_record('product.product', product.id)
        return res


    def unlink(self):
        for product_temp in self:
            products = self.env['product.product'].search([('product_tmpl_id', '=', product_temp.id)])
            for product in products:
                self.env['pos.cache.database'].remove_record('product.product', product.id)
        return super(product_template, self).unlink()


class product_product(models.Model):

    _inherit = 'product.product'

    def write(self, vals):
        res = super(product_product, self).write(vals)
        for product in self:
            if product.available_in_pos and product.active:
                self.env['pos.cache.database'].insert_data('product.product', product.id)
            if not product.available_in_pos or not product.active:
                self.env['pos.cache.database'].remove_record(self._inherit, product.id)
        return res

    @api.model
    def create(self, vals):
        product = super(product_product, self).create(vals)
        if product.sale_ok and product.available_in_pos:
            self.env['pos.cache.database'].insert_data(self._inherit, product.id)
        return product

    def unlink(self):
        for product in self:
            self.env['pos.cache.database'].remove_record(self._inherit, product.id)
        return super(product_product, self).unlink()
