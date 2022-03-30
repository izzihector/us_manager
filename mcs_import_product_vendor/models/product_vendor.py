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


class mcs_tampungan(models.Model):
    _name 				= 'mcs.tampungan.import'
    _description 		= 'MCS | Import vendor products'

    name                = fields.Char(string='Name')
    kode       			= fields.Char('Kode Session')
    vendor_product_id 	= fields.Many2one("vendor.product", string="Vendor Product")
    product_tmpl_id 		= fields.Many2one("product.template", string="Product Template")
    partner_id 			= fields.Many2one("res.partner", string="Vendor")
    brand_id 				= fields.Many2one("product.brand", string="Brand")
    location_id 			= fields.Many2one("vendor.location", string="Location")
    branch_id 				= fields.Many2one("res.branch", string="Branch")
    pricelist_id 			= fields.Many2one("product.pricelist", string="pricelist")
    portal_input_price 	= fields.Float(string="portal_input_price")
    price_after_margin 	= fields.Float(string="price_after_margin")
    margin_percentage 	= fields.Float(string="Margin")

class mcs_produk_vendor(models.TransientModel):
	_name 		 	= "mcs.import.produk.vendor"
	_description 	= 'MCS | Import vendor products'

	partner_id 		= fields.Many2one("res.partner", string="Vendor", required=True)
	nama_file       = fields.Binary(string="Select File",required=True)
	file_name       = fields.Char('File Name')

	def act_import_data(self):
		fp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
		fp.write(binascii.a2b_base64(self.nama_file))
		fp.seek(0)
		workbook = xlrd.open_workbook(fp.name)
		sheet = workbook.sheet_by_index(0)
		output = []
		for row_no in range(sheet.nrows):
			values = {}
			values_line = {}
			if row_no <= 0:
				fields = map(lambda row:row.value.encode('utf-8'), sheet.row(row_no))
			else:
				line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value),sheet.row(row_no)))
				CekBrand      = self.env['product.brand'].sudo().search([('name', '=', line[3])],limit=1)
				if CekBrand:
					CekKategori = self.env['product.category'].sudo().search([('complete_name', '=', line[4])],limit=1)
					if CekKategori:
						CekUom = self.env['uom.uom'].sudo().search([('name', '=', line[5])],limit=1)
						if CekUom:
							Branch = self.env['res.branch'].sudo().search([('name', '=', line[8])],limit=1)
							if Branch:
								Pricelist = self.env['product.pricelist'].sudo().search([('name', '=', line[9])],limit=1)
								if Pricelist:
									Location = self.env['vendor.location'].sudo().search([('name', '=', line[7])],limit=1)
									if Location:
										if line[0] == 'Product':
											# create produk template
											CreateProductTemplate = self.env['product.template'].create({
																										'name'              	: line[2], 
			                                                                  	'sale_ok'        		: 't', 
			                                                                  	'is_consignment'  	: 't', 
			                                                                  	'is_autonaming'  		: 't', 
			                                                                  	'brand_id'  			: CekBrand.id, 
			                                                                  	'categ_id' 				: CekKategori.id, 
			                                                                  	'owner_id' 				: self.partner_id.id, 
			                                                                  	'list_price' 			: line[10], 
			                                                                  	'margin' 				: CekBrand.consignment_margin, 
			                                                                  	'uom_id' 				: CekUom.id, 
			                                                                  	'uom_po_id' 			: CekUom.id, 
			                                                                  	'type' 					: 'product', 
			                                                                  	'tracking' 				: 'none', 
			                                                                  	'sale_line_warn'		: 'no-message', 
			                                                                  	'purchase_line_warn'	: 'no-message'
																			})
											# create produk vendor
											CreateProductVendor = self.env['vendor.product'].create({
			                                                                  	'product_name'          : line[2], 
			                                                                  	'margin_percentage'     : CekBrand.consignment_margin, 
			                                                                  	'partner_id'        		: self.partner_id.id, 
			                                                                  	'product_category_id'	: CekKategori.id, 
			                                                                  	'product_uom_id'   		: CekUom.id, 
			                                                                  	'product_brand_id'   	: CekBrand.id, 
			                                                                  	'product_tmpl_id'    	: CreateProductTemplate.id, 
			                                                                  	'company_id'            : 1,
			                                                                  	'state'        			: line[6],
			                                                                  	'active'            		: 't'
			                                                                })
											# create tampungan
											Createtampungan = self.env['mcs.tampungan.import'].create({
		                                                                      	'name'              	: 'Data Import', 
		                                                                      	'kode'					: line[1],
		                                                                      	'product_tmpl_id' 	: CreateProductTemplate.id,
		                                                                      	'vendor_product_id'  : CreateProductVendor.id, 
		                                                                      	'partner_id'  			: self.partner_id.id, 
		                                                                      	'brand_id'  			: CekBrand.id, 
		                                                                      	'location_id'  		: Location.id, 
		                                                                      	'branch_id'  			: Branch.id, 
		                                                                      	'pricelist_id'  		: Pricelist.id, 
		                                                                      	'portal_input_price' : line[10], 
		                                                                      	'margin_percentage'  : CekBrand.consignment_margin,
			                                                                    })
										elif line[0] == 'Variant':
											CekTampungan = self.env['mcs.tampungan.import'].sudo().search([('kode', '=', line[1])],limit=1)
											if CekTampungan:
												# cek atribut utk create varian
												

												# CREATE PRODUK VARIANT
												ProductProduk = self.env['product.product'].create({
				                                                               			'product_tmpl_id'    	: CreateProductTemplate.id, 
				                                                               			'company_id'            : 1,
				                                                               			'brand_id'  				: CekBrand.id, 
				                                                                    })
												# Create Product Varian
												ProductVariant = self.env['vendor.product.variant'].create({
			                                                               			'partner_id'        		: self.partner_id.id, 
			                                                                      	'vendor_product_id'     : CreateProductVendor.id, 
			                                                               			'product_name'          : line[2], 
			                                                                  		'product_id'     			: ProductProduk.id,
			                                                               			'product_tmpl_id'    	: CreateProductTemplate.id, 
			                                                               			'company_id'            : 1,
			                                                               			'active'            		: 't',
			                                                                    })

												CekWarna = self.env['product.attribute.value'].sudo().search([('name', '=', line[11])],limit=1)
												if CekWarna:
													# warna ada
													ProductVariant.attribute_value_ids 	=  [(4, CekWarna.id)]

													CekAttributLine = self.env['vendor.product.attr.line'].sudo().search([('vendor_product_id', '=', CekTampungan.vendor_product_id.id),('attribute_id', '=', 1)],limit=1)
													if CekAttributLine:
														# jika atribute ada maka di edit untk nambahkan value di attribute yg sama
														# edit variant yg ada
														ValueWarna = self.env['product.attribute.value'].sudo().search([('name', '=', line[11].replace(".0", ""))],limit=1)
														CekAttributLine.value_ids = [(4, ValueWarna.id)]

													else:
														# cek atribut utk create varian
														ValueWarna = self.env['product.attribute.value'].sudo().search([('name', '=', line[11].replace(".0", ""))],limit=1)
														CreateAttruteid = self.env['vendor.product.attr.line'].create({
					                                                                      	'vendor_product_id'     : CekTampungan.vendor_product_id.id, 
					                                                                  		'attribute_id'     		: 1,
					                                                                    })

														CreateAttruteid.value_ids =  [(4, ValueWarna.id)]


												else:
													print("=========== WARNA TAK ADA")

												CekSize = self.env['product.attribute.value'].sudo().search([('name', '=', line[12].replace(".0", ""))],limit=1)
												if CekSize:
													# warna ada
													ProductVariant.attribute_value_ids 	=  [(4, CekSize.id)]

													CekAttributLine = self.env['vendor.product.attr.line'].sudo().search([('vendor_product_id', '=', CekTampungan.vendor_product_id.id),('attribute_id', '=', 5)],limit=1)
													if CekAttributLine:
														# jika atribute ada maka di edit untk nambahkan value di attribute yg sama
														# edit variant yg ada
														ValueSize = self.env['product.attribute.value'].sudo().search([('name', '=', line[12].replace(".0", ""))],limit=1)
														CekAttributLine.value_ids = [(4, ValueSize.id)]

													else:
														# cek atribut utk create varian
														ValueSize = self.env['product.attribute.value'].sudo().search([('name', '=', line[12].replace(".0", ""))],limit=1)
														CreateAttruteid = self.env['vendor.product.attr.line'].create({
					                                                                      	'vendor_product_id'     : CekTampungan.vendor_product_id.id, 
					                                                                  		'attribute_id'     		: 5,
					                                                                    })

														CreateAttruteid.value_ids =  [(4, ValueSize.id)]


												else:
													print("=========== SIZE TAK ADA")
													# warna tidak ada

												CekModel = self.env['product.attribute.value'].sudo().search([('name', '=', line[13])],limit=1)
												if CekModel:
													# warna ada
													ProductVariant.attribute_value_ids 	=  [(4, CekModel.id)]

													CekAttributLine = self.env['vendor.product.attr.line'].sudo().search([('vendor_product_id', '=', CekTampungan.vendor_product_id.id),('attribute_id', '=', 2)],limit=1)
													if CekAttributLine:
														# jika atribute ada maka di edit untk nambahkan value di attribute yg sama
														# edit variant yg ada
														ValueModel = self.env['product.attribute.value'].sudo().search([('name', '=', line[13].replace(".0", ""))],limit=1)
														CekAttributLine.value_ids = [(4, ValueModel.id)]

													else:
														# cek atribut utk create varian
														ValueModel = self.env['product.attribute.value'].sudo().search([('name', '=', line[13].replace(".0", ""))],limit=1)
														CreateAttruteid = self.env['vendor.product.attr.line'].create({
					                                                                      	'vendor_product_id'     : CekTampungan.vendor_product_id.id, 
					                                                                  		'attribute_id'     		: 2,
					                                                                    })

														CreateAttruteid.value_ids =  [(4, ValueModel.id)]



												else:
													print("=========== MODEL TAK ADA")
													# warna tidak ada

												CekTema = self.env['product.attribute.value'].sudo().search([('name', '=', line[14])],limit=1)
												if CekTema:
													# warna ada
													ProductVariant.attribute_value_ids 	=  [(4, CekTema.id)]

													CekAttributLine = self.env['vendor.product.attr.line'].sudo().search([('vendor_product_id', '=', CekTampungan.vendor_product_id.id),('attribute_id', '=', 6)],limit=1)
													if CekAttributLine:
														# jika atribute ada maka di edit untk nambahkan value di attribute yg sama
														# edit variant yg ada
														ValueTema = self.env['product.attribute.value'].sudo().search([('name', '=', line[14].replace(".0", ""))],limit=1)
														CekAttributLine.value_ids = [(4, ValueTema.id)]

													else:
														# cek atribut utk create varian
														ValueTema = self.env['product.attribute.value'].sudo().search([('name', '=', line[14].replace(".0", ""))],limit=1)
														CreateAttruteid = self.env['vendor.product.attr.line'].create({
					                                                                      	'vendor_product_id'     : CekTampungan.vendor_product_id.id, 
					                                                                  		'attribute_id'     		: 6,
					                                                                    })

														CreateAttruteid.value_ids =  [(4, ValueTema.id)]


												else:
													print("=========== TEMA TAK ADA")
													# warna tidak ada

												CekMotif = self.env['product.attribute.value'].sudo().search([('name', '=', line[15])],limit=1)
												if CekMotif:
													# warna ada
													ProductVariant.attribute_value_ids 	=  [(4, CekMotif.id)]
													CekAttributLine = self.env['vendor.product.attr.line'].sudo().search([('vendor_product_id', '=', CekTampungan.vendor_product_id.id),('attribute_id', '=', 3)],limit=1)
													if CekAttributLine:
														# jika atribute ada maka di edit untk nambahkan value di attribute yg sama
														# edit variant yg ada
														ValueMotif = self.env['product.attribute.value'].sudo().search([('name', '=', line[15].replace(".0", ""))],limit=1)
														CekAttributLine.value_ids = [(4, ValueMotif.id)]

													else:
														# cek atribut utk create varian
														ValueMotif = self.env['product.attribute.value'].sudo().search([('name', '=', line[15].replace(".0", ""))],limit=1)
														CreateAttruteid = self.env['vendor.product.attr.line'].create({
					                                                                      	'vendor_product_id'     : CekTampungan.vendor_product_id.id, 
					                                                                  		'attribute_id'     		: 3,
					                                                                    })

														CreateAttruteid.value_ids =  [(4, ValueMotif.id)]

												else:
													print("=========== MOTIF TAK ADA")
													# warna tidak ada

												CekBahan = self.env['product.attribute.value'].sudo().search([('name', '=', line[16])],limit=1)
												if CekBahan:
													# warna ada
													ProductVariant.attribute_value_ids 	=  [(4, CekBahan.id)]

													CekAttributLine = self.env['vendor.product.attr.line'].sudo().search([('vendor_product_id', '=', CekTampungan.vendor_product_id.id),('attribute_id', '=', 10)],limit=1)
													if CekAttributLine:
														# jika atribute ada maka di edit untk nambahkan value di attribute yg sama
														# edit variant yg ada
														ValueBahan = self.env['product.attribute.value'].sudo().search([('name', '=', line[16].replace(".0", ""))],limit=1)
														CekAttributLine.value_ids = [(4, ValueBahan.id)]

													else:
														# cek atribut utk create varian
														ValueBahan = self.env['product.attribute.value'].sudo().search([('name', '=', line[16].replace(".0", ""))],limit=1)
														CreateAttruteid = self.env['vendor.product.attr.line'].create({
					                                                                      	'vendor_product_id'     : CekTampungan.vendor_product_id.id, 
					                                                                  		'attribute_id'     		: 10,
					                                                                    })

														CreateAttruteid.value_ids =  [(4, ValueBahan.id)]


												else:
													print("=========== BAHAN TAK ADA")
													# warna tidak ada

												# Create Product Supplier
												ProductSupplier = self.env['product.supplierinfo'].create({
			                                                                      	'vendor_product_id'     		: CreateProductVendor.id, 
			                                                               			'vendor_product_variant_id'   : ProductVariant.id, 
			                                                               			'name'   							: self.partner_id.name, 
			                                                                  		'product_id'     					: ProductProduk.id,
			                                                               			'location_id'  					: Location.id, 
			                                                               			'branch_id'  						: Branch.id, 
			                                                               			'pricelist_id'  					: Pricelist.id, 
			                                                               			'delay'            				: 0,
			                                                               			'company_id'            		: 1,
			                                                               			'portal_input_price' 			: line[10], 
			                                                               			'margin_percentage' 				: CekBrand.consignment_margin,
			                                                               			'active'            				: 't',
			                                                                    })

									else:
										raise ValidationError(('LOCATION TIDAK DITEMUKAN PADA MASTER DATA : ',line[7]))
								else:
									raise ValidationError(('PRICELIST TIDAK DITEMUKAN PADA MASTER DATA : ',line[9]))
							else:
								raise ValidationError(('BRANCH TIDAK DITEMUKAN PADA MASTER DATA : ',line[8]))
						else:
							raise ValidationError(('UNIT OF MEASURE TIDAK DITEMUKAN PADA MASTER DATA : ',line[5]))
					else:
						raise ValidationError(('KATEGORI PRODUK TIDAK DITEMUKAN PADA MASTER DATA : ',line[4]))
				else:
					raise ValidationError(('BRAND TIDAK DITEMUKAN PADA MASTER DATA : ',line[3]))

		self.env.cr.execute(""" DELETE FROM mcs_tampungan_import""", ())


