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

		noLogger = 1

		for row_no in range(sheet.nrows):
			_logger.warn("=================================")
			_logger.warn(noLogger)
			_logger.warn(datetime.now())
			noLogger += 1
			
			values = {}
			values_line = {}
			if row_no <= 0:
				fields = map(lambda row:row.value.encode('utf-8'), sheet.row(row_no))
			else:
				line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value),sheet.row(row_no)))

				cr = self.env.cr
				cr.execute("""
					SELECT id, name, consignment_margin
					FROM product_brand
					WHERE name='%s'
					LIMIT 1
				""" % (line[3]))
				CekBrand = cr.fetchone()

				if CekBrand:
					cr.execute("""
						SELECT id, complete_name
						FROM product_category
						WHERE complete_name='%s'
						LIMIT 1
					""" % (line[4]))
					CekKategori = cr.fetchone()
					if CekKategori:
						cr.execute("""
							SELECT id, name
							FROM uom_uom
							WHERE name='%s'
								LIMIT 1
						""" % (line[5]))
						CekUom = cr.fetchone()
						if CekUom:
							cr.execute("""
								SELECT id, name
								FROM res_branch
								WHERE name='%s'
								LIMIT 1
							""" % (line[8]))
							Branch = cr.fetchone()
							if Branch:
								cr.execute("""
									SELECT id, name
									FROM product_pricelist
									WHERE name='%s'
									LIMIT 1
								""" % (line[9]))
								Pricelist = cr.fetchone()
								if Pricelist:
									cr.execute("""
										SELECT id, name
										FROM vendor_location
										WHERE name='%s'
										LIMIT 1
									""" % (line[7]))
									Location = cr.fetchone()
									if Location:
										if line[0] == 'Product':
											# create produk template
											# CreateProductTemplate = self.env['product.template'].create({
											# 									'name'              	: line[2], 
			                                #                                   	'sale_ok'        		: 't', 
			                                #                                   	'is_consignment'  	: 't', 
			                                #                                   	'is_autonaming'  		: 't', 
			                                #                                   	'brand_id'  			: CekBrand[0], 
			                                #                                   	'categ_id' 				: CekKategori[0], 
			                                #                                   	'owner_id' 				: self.partner_id.id, 
			                                #                                   	'list_price' 			: line[10], 
			                                #                                   	'margin' 				: 0, 
			                                #                                   	'uom_id' 				: CekUom[0], 
			                                #                                   	'uom_po_id' 			: CekUom[0], 
			                                #                                   	'type' 					: 'product', 
			                                #                                   	'tracking' 				: 'none', 
			                                #                                   	'sale_line_warn'		: 'no-message', 
			                                #                                   	'purchase_line_warn'	: 'no-message'
											# 								})
											cr.execute("""
													INSERT INTO product_template(name, sale_ok, is_consignment, is_autonaming, brand_id, categ_id, owner_id, list_price, margin, uom_id, uom_po_id, type, tracking, sale_line_warn, purchase_line_warn)
													VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);
													SELECT MAX(id) FROM product_template;
												""", (line[2], 't', 't', 't', CekBrand[0], CekKategori[0], self.partner_id.id, line[10] or 0, 0, CekUom[0], CekUom[0], 'product', 'none', 'no-message', 'no-message'))
											CreateProductTemplate = cr.fetchone()

											# create produk vendor
											# CreateProductVendor = self.env['vendor.product'].create({
			                                #                                   	'product_name'          : line[2], 
			                                #                                   	'margin_percentage'     : 0, 
			                                #                                   	'partner_id'        		: self.partner_id.id, 
			                                #                                   	'product_category_id'	: CekKategori[0], 
			                                #                                   	'product_uom_id'   		: CekUom[0], 
			                                #                                   	'product_brand_id'   	: CekBrand[0], 
			                                #                                   	'product_tmpl_id'    	: CreateProductTemplate[0], 
			                                #                                   	'company_id'            : 1,
			                                #                                   	'state'        			: line[6],
			                                #                                   	'active'            		: 't'
			                                #                                 })
											cr.execute("""
													INSERT INTO vendor_product(
														product_name,
														margin_percentage,
														partner_id,
														product_category_id,
														product_uom_id,
														product_brand_id,
														product_tmpl_id,
														company_id,
														state,
														active
														)
													VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);
													SELECT MAX(id) FROM vendor_product;
												""", (
													line[2],
													CekBrand[2],
													self.partner_id.id,
													CekKategori[0],
													CekUom[0], 
													CekBrand[0], 
													CreateProductTemplate[0],
													1,
													line[6],
													 't'
												))
											CreateProductVendor = cr.fetchone()

											# create tampungan
											# Createtampungan = self.env['mcs.tampungan.import'].create({
		                                    #                                   	'name'              	: 'Data Import', 
		                                    #                                   	'kode'					: line[1],
		                                    #                                   	'product_tmpl_id' 	: CreateProductTemplate[0],
		                                    #                                   	'vendor_product_id'  : CreateProductVendor[0], 
		                                    #                                   	'partner_id'  			: self.partner_id.id, 
		                                    #                                   	'brand_id'  			: CekBrand[0], 
		                                    #                                   	'location_id'  		: Location[0], 
		                                    #                                   	'branch_id'  			: Branch[0], 
		                                    #                                   	'pricelist_id'  		: Pricelist[0], 
		                                    #                                   	'portal_input_price' : line[10], 
		                                    #                                   	'margin_percentage'  : 0,
			                                #                                     })
											cr.execute("""
													INSERT INTO mcs_tampungan_import(
														name,
														kode,
														product_tmpl_id,
														vendor_product_id,
														partner_id,
														brand_id,
														location_id,
														branch_id,
														pricelist_id,
														portal_input_price,
														margin_percentage
														)
													VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);
												""", (
													'Data Import', 
													line[1],
													CreateProductTemplate[0],
													CreateProductVendor[0], 
													self.partner_id.id, 
													CekBrand[0], 
													Location[0], 
													Branch[0], 
													Pricelist[0], 
													line[10] or 0, 
													CekBrand[2]
												))
										elif line[0] == 'Variant':
											cr.execute("""
												SELECT id, name, vendor_product_id
												FROM mcs_tampungan_import
												WHERE kode='%s'
												LIMIT 1
											""" % (line[1]))
											CekTampungan = cr.fetchone()
											if CekTampungan:
												# cek atribut utk create varian
												

												# CREATE PRODUK VARIANT
												ProductProduk = self.env['product.product'].create({
				                                                               			'product_tmpl_id'    	: CreateProductTemplate[0], 
				                                                               			'company_id'            : 1,
				                                                               			'brand_id'  				: CekBrand[0], 
				                                                                    })
												# Create Product Varian
												ProductVariant = self.env['vendor.product.variant'].create({
			                                                               			'partner_id'        		: self.partner_id.id, 
			                                                                      	'vendor_product_id'     : CreateProductVendor[0], 
			                                                               			'product_name'          : line[2], 
			                                                                  		'product_id'     			: ProductProduk.id,
			                                                               			'product_tmpl_id'    	: CreateProductTemplate[0], 
			                                                               			'company_id'            : 1,
			                                                               			'active'            		: 't',
			                                                                    })

												cr.execute("""
													SELECT id
													FROM product_attribute_value
													WHERE name='%s'
													LIMIT 1
												""" % (line[11]))
												CekWarna = cr.fetchone()
												if CekWarna:
													# warna ada
													ProductVariant.attribute_value_ids 	=  [(4, CekWarna[0])]

													CekAttributLine = self.env['vendor.product.attr.line'].sudo().search([('vendor_product_id', '=', CekTampungan[2]),('attribute_id', '=', 1)],limit=1)
													
													if CekAttributLine:
														# jika atribute ada maka di edit untk nambahkan value di attribute yg sama
														# edit variant yg ada
														CekAttributLine.value_ids = [(4, CekWarna[0])]

													else:
														# cek atribut utk create varian
														CreateAttruteid = self.env['vendor.product.attr.line'].create({
					                                                                      	'vendor_product_id'     : CekTampungan[2], 
					                                                                  		'attribute_id'     		: 1,
					                                                                    })

														CreateAttruteid.value_ids = [(4, CekWarna[0])]


												else:
													print("=========== WARNA TAK ADA")

												cr.execute("""
													SELECT id
													FROM product_attribute_value
													WHERE name='%s'
													LIMIT 1
												""" % (line[12]))
												CekSize = cr.fetchone()
												if CekSize:
													# warna ada
													ProductVariant.attribute_value_ids 	=  [(4, CekSize[0])]

													CekAttributLine = self.env['vendor.product.attr.line'].sudo().search([('vendor_product_id', '=', CekTampungan[2]),('attribute_id', '=', 5)],limit=1)
													if CekAttributLine:
														# jika atribute ada maka di edit untk nambahkan value di attribute yg sama
														# edit variant yg ada
														CekAttributLine.value_ids = [(4, CekSize[0])]

													else:
														# cek atribut utk create varian
														CreateAttruteid = self.env['vendor.product.attr.line'].create({
					                                                                      	'vendor_product_id'     : CekTampungan[2], 
					                                                                  		'attribute_id'     		: 5,
					                                                                    })

														CreateAttruteid.value_ids =  [(4, CekSize[0])]


												else:
													print("=========== SIZE TAK ADA")
													# warna tidak ada

												cr.execute("""
													SELECT id
													FROM product_attribute_value
													WHERE name='%s'
													LIMIT 1
												""" % (line[13]))
												CekModel = cr.fetchone()
												if CekModel:
													# warna ada
													ProductVariant.attribute_value_ids 	=  [(4, CekModel[0])]

													CekAttributLine = self.env['vendor.product.attr.line'].sudo().search([('vendor_product_id', '=', CekTampungan[2]),('attribute_id', '=', 2)],limit=1)
													if CekAttributLine:
														# jika atribute ada maka di edit untk nambahkan value di attribute yg sama
														# edit variant yg ada
														CekAttributLine.value_ids = [(4, CekModel[0])]

													else:
														# cek atribut utk create varian
														CreateAttruteid = self.env['vendor.product.attr.line'].create({
					                                                                      	'vendor_product_id'     : CekTampungan[2], 
					                                                                  		'attribute_id'     		: 2,
					                                                                    })

														CreateAttruteid.value_ids =  [(4, CekModel[0])]



												else:
													print("=========== MODEL TAK ADA")
													# warna tidak ada

												cr.execute("""
													SELECT id
													FROM product_attribute_value
													WHERE name='%s'
													LIMIT 1
												""" % (line[14]))
												CekTema = cr.fetchone()
												if CekTema:
													# warna ada
													ProductVariant.attribute_value_ids 	=  [(4, CekTema[0])]

													CekAttributLine = self.env['vendor.product.attr.line'].sudo().search([('vendor_product_id', '=', CekTampungan[2]),('attribute_id', '=', 6)],limit=1)
													if CekAttributLine:
														# jika atribute ada maka di edit untk nambahkan value di attribute yg sama
														# edit variant yg ada
														CekAttributLine.value_ids = [(4, CekTema[0])]

													else:
														# cek atribut utk create varian
														CreateAttruteid = self.env['vendor.product.attr.line'].create({
					                                                                      	'vendor_product_id'     : CekTampungan[2], 
					                                                                  		'attribute_id'     		: 6,
					                                                                    })

														CreateAttruteid.value_ids =  [(4, CekTema[0])]


												else:
													print("=========== TEMA TAK ADA")
													# warna tidak ada

												cr.execute("""
													SELECT id
													FROM product_attribute_value
													WHERE name='%s'
													LIMIT 1
												""" % (line[15]))
												CekMotif = cr.fetchone()
												if CekMotif:
													# warna ada
													ProductVariant.attribute_value_ids 	=  [(4, CekMotif[0])]
													CekAttributLine = self.env['vendor.product.attr.line'].sudo().search([('vendor_product_id', '=', CekTampungan[2]),('attribute_id', '=', 3)],limit=1)
													if CekAttributLine:
														# jika atribute ada maka di edit untk nambahkan value di attribute yg sama
														# edit variant yg ada
														CekAttributLine.value_ids = [(4, CekMotif[0])]

													else:
														# cek atribut utk create varian
														CreateAttruteid = self.env['vendor.product.attr.line'].create({
					                                                                      	'vendor_product_id'     : CekTampungan[2], 
					                                                                  		'attribute_id'     		: 3,
					                                                                    })

														CreateAttruteid.value_ids =  [(4, CekMotif[0])]

												else:
													print("=========== MOTIF TAK ADA")
													# warna tidak ada

												cr.execute("""
													SELECT id
													FROM product_attribute_value
													WHERE name='%s'
													LIMIT 1
												""" % (line[16]))
												CekBahan = cr.fetchone()
												if CekBahan:
													# warna ada
													ProductVariant.attribute_value_ids 	=  [(4, CekBahan[0])]

													CekAttributLine = self.env['vendor.product.attr.line'].sudo().search([('vendor_product_id', '=', CekTampungan[2]),('attribute_id', '=', 10)],limit=1)
													if CekAttributLine:
														# jika atribute ada maka di edit untk nambahkan value di attribute yg sama
														# edit variant yg ada
														CekAttributLine.value_ids = [(4, CekBahan[0])]

													else:
														# cek atribut utk create varian
														CreateAttruteid = self.env['vendor.product.attr.line'].create({
					                                                                      	'vendor_product_id'     : CekTampungan[2], 
					                                                                  		'attribute_id'     		: 10,
					                                                                    })

														CreateAttruteid.value_ids =  [(4, CekBahan[0])]


												else:
													print("=========== BAHAN TAK ADA")
													# warna tidak ada

												# Create Product Supplier
												ProductSupplier = self.env['product.supplierinfo'].create({
			                                                                      	'vendor_product_id'     		: CreateProductVendor[0], 
			                                                               			'vendor_product_variant_id'   : ProductVariant.id, 
			                                                               			'name'   							: self.partner_id.name, 
			                                                                  		'product_id'     					: ProductProduk.id,
			                                                               			'location_id'  					: Location[0], 
			                                                               			'branch_id'  						: Branch[0], 
			                                                               			'pricelist_id'  					: Pricelist[0], 
			                                                               			'delay'            				: 0,
			                                                               			'company_id'            		: 1,
			                                                               			'portal_input_price' 			: line[10], 
			                                                               			'margin_percentage' 				: CekBrand[2],
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


