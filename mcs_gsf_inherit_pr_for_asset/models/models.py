# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PurchaseRequisition(models.Model):
    _inherit = 'replenish.request'

    is_asset = fields.Boolean('Asset')


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    is_asset = fields.Boolean('Asset')

class AccountMove(models.Model):
    _inherit = 'account.move'

    is_asset = fields.Boolean('Asset')