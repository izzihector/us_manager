# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _

class pos_config(models.Model):
    _inherit = 'pos.config'

    pos_bag_category_id = fields.Many2one('pos.category','Bag Charges Category')
    allow_bag_charges = fields.Boolean('Allow Bag Charges')

	
	

