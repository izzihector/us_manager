# -*- coding: utf-8 -*-

# ===================================================
# |     Developmeny By : Brata Bayu S, S.Kom        |
# ===================================================


from odoo.exceptions import UserError, AccessError, ValidationError
from openerp.exceptions import except_orm, Warning, RedirectWarning
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import Warning
import binascii
import tempfile
import xlrd
from tempfile import TemporaryFile
import logging
import itertools

_logger = logging.getLogger(__name__)
import io

try:
    import xlrd
except ImportError:
    _logger.debug('Cannot `import xlrd`.')

try:
    import base64
except ImportError:
    _logger.debug('Cannot `import base64`.')



# class brt_delete_vendor_product_wizard(models.TransientModel):
class brt_delete_vendor_product_wizard(models.TransientModel):
	_name 			= 'brt.delete_product_vendor'
	_description 	= 'Delete Product Vendor'

	name                = fields.Char(string='Name')

	def action_delete_product_vendor(self):
		vendor_product_ids 		= self.env['vendor.product'].browse(self._context.get('active_ids', []))
		for rec in vendor_product_ids:
			self.env.cr.execute("""
                         SELECT s.* FROM vendor_product_variant s WHERE s.vendor_product_id = %s
                         """,(int(rec.id),))
			get_no_max  = self.env.cr.dictfetchall()
			for data in get_no_max :
				self.env.cr.execute(""" DELETE FROM product_supplierinfo WHERE vendor_product_variant_id = %s""", (int(data['id']),))
				self.env.cr.execute(""" DELETE FROM vendor_product_variant WHERE id = %s""", (int(data['id']),))
			
			self.env.cr.execute("""
                            SELECT s.* FROM vendor_product_attr_line s WHERE s.vendor_product_id = %s
                            """,(int(rec.id),))
			get_no_max  = self.env.cr.dictfetchall()
			for data in get_no_max :
				self.env.cr.execute(""" DELETE FROM vendor_product_attr_line WHERE id = %s""", (int(data['id']),))
				
			self.env.cr.execute(""" DELETE FROM vendor_product WHERE id = %s""", (int(rec.id),))
				
class brt_delete_variant_product_wizard(models.TransientModel):
	_name 			= 'brt.delete_product_variant'
	_description 	= 'Delete Product Variant'

	name                = fields.Char(string='Name')

	def action_delete_product_variant(self):
		product_ids 		= self.env['product.product'].browse(self._context.get('active_ids', []))
		for rec in product_ids:
			self.env.cr.execute(""" DELETE FROM product_product WHERE id = %s""", (int(rec.id),))