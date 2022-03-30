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


class mcs_tampungan_do(models.Model):
    _name 				= 'mcs.tampungan.import.do'
    _description 		= 'MCS | Tampungan Import vendor products + DO'

    name                = fields.Char(string='Name')
    kode       			= fields.Integer('Kode Session')
    vendor_product_id 	= fields.Many2one("vendor.product", string="Vendor Product")
    id_do 				= fields.Many2one("vendor.stock.picking", string="DO ID")
    product_tmpl_id 	= fields.Many2one("product.template", string="Product Template")
    partner_id 			= fields.Many2one("res.partner", string="Vendor")
    brand_id 			= fields.Many2one("product.brand", string="Brand")
    location_id 		= fields.Many2one("vendor.location", string="Location")
    branch_id 			= fields.Many2one("res.branch", string="Branch")
    pricelist_id 		= fields.Many2one("product.pricelist", string="pricelist")
    portal_input_price 	= fields.Float(string="portal_input_price")
    price_after_margin 	= fields.Float(string="price_after_margin")
    margin_percentage 	= fields.Float(string="Margin")

class mcs_produk_vendor_do(models.TransientModel):
	_name 		 	= "mcs.import.produk.vendor.do"
	_description 	= 'MCS | Import vendor products + DO'

	partner_id 		= fields.Many2one("res.partner", string="Vendor", required=True)
	nama_file       = fields.Binary(string="Select File",required=True)
	file_name       = fields.Char('File Name')


	def act_clear_data(self):
		self.env.cr.execute(""" DELETE FROM mcs_tampungan_import_do""", ())


	def act_import_data_do(self):
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
											cr.execute("""
													INSERT INTO product_template(name, sale_ok, is_consignment, is_autonaming, is_published, available_in_pos, brand_id, categ_id, owner_id, list_price, margin, uom_id, uom_po_id, type, tracking, sale_line_warn, active, purchase_line_warn)
													VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);
													SELECT MAX(id) FROM product_template;
												""", (line[2], 't', 't', 't', 't', 'f', CekBrand[0], CekKategori[0], self.partner_id.id, line[10] or 0, CekBrand[2], CekUom[0], CekUom[0], 'product', 'none', 'no-message', 't', 'no-message'))
											CreateProductTemplate = cr.fetchone()
											
											# create produk vendor
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
													SELECT MAX(id), product_code FROM vendor_product GROUP BY product_code;
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

											self.env.cr.execute(""" UPDATE product_template SET default_code = %s, active = %s WHERE id = %s""", ( CreateProductVendor[1], True, CreateProductTemplate[0],))

											cr.execute("""
												SELECT id
												FROM product_product
												WHERE product_tmpl_id='%s'
												LIMIT 1
											""" % (CreateProductTemplate[0]))
											prdprd = cr.fetchone()
											if prdprd:
												self.env.cr.execute(""" DELETE FROM product_product WHERE id = %s""", ( prdprd[0] ))


											get_thn_now = str(datetime.now().strftime("%Y"))
											self.env.cr.execute(""" SELECT  MAX(s.id) AS no_max FROM vendor_stock_picking s """,())
											get_no_max  = self.env.cr.dictfetchall()
											sequence = 1
											for data in get_no_max :
												if data['no_max'] :
													sequence = int(data['no_max']) + 1
												else:
													sequence = 1 

											namedo = 'VSP'+str(sequence)
											CreateHeaderDo = self.env['vendor.stock.picking'].create({
                                                                      	'name'              	: namedo, 
                                                                      	'partner_id'			: self.partner_id.id,
                                                                      	'vendor_location_id'	: Location[0],
                                                                      	'operation_type'  		: 'incoming', 
                                                                      	'state'  				: 'draft', 
                                                                    })
											cr.execute("""
													INSERT INTO vendor_stock_picking(
														name,
														partner_id,
														vendor_location_id,
														operation_type,
														state
														)
													VALUES (%s,%s,%s,%s,%s);
													SELECT MAX(id) FROM vendor_stock_picking;
												""", (
													namedo,
													self.partner_id.id,
													Location[0],
													'incoming', 
													'draft'
												))
											CreateHeaderDo = cr.fetchone()
											kode = str(line[1].replace(".0", ""))
											# create tampungan
											cr.execute("""
													INSERT INTO mcs_tampungan_import_do(
														name,
														kode,
														id_do,
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
													VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);
												""", (
													'Data Import', 
													int(kode),
													CreateHeaderDo[0],
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

											print("============================================ TEMPLATE ID 1 : ",CreateProductTemplate[0],)
										elif line[0] == 'Variant':
											kode = str(line[1].replace(".0", ""))
											cr.execute("""
												SELECT id, product_tmpl_id, vendor_product_id, id_do
												FROM mcs_tampungan_import_do
												WHERE kode='%s'
												LIMIT 1
											""" % (int(kode)))
											CekTampungan = cr.fetchone()
											if CekTampungan:

												# CREATE PRODUK VARIANT
												BuatProduk = self.env['product.product'].sudo().create({
				                                                               			'product_tmpl_id'    	: CekTampungan[1], 
				                                                               			'company_id'            : 1,
				                                                               			'brand_id'  			: CekBrand[0], 
				                                                               			# 'combination_indices'	: 1,
				                                                                    })

												BuatProduk.combination_indices 	= CekTampungan[0]
												# Create Product Varian
												ProductVariant = self.env['vendor.product.variant'].sudo().create({
			                                                               			'partner_id'        	: self.partner_id.id, 
			                                                                      	'vendor_product_id'     : CekTampungan[2], 
			                                                               			'product_name'          : line[2], 
			                                                                  		'product_id'     		: BuatProduk.id,
			                                                               			'product_tmpl_id'    	: CekTampungan[1], 
			                                                               			'company_id'            : 1,
			                                                               			'active'            	: 't',
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

														CreateAttruteid.value_ids =  [(4, CekWarna[0])]

												else:
													print("=========== WARNA TAK ADA")

												cr.execute("""
													SELECT id
													FROM product_attribute_value
													WHERE name='%s'
													LIMIT 1
												""" % (line[12].replace(".0", "")))
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

												CreateStokLine = self.env['vendor.stock.move'].create({
			                                                                      	'name'     						: line[2], 
			                                                               			'partner_id'   					: self.partner_id.id, 
			                                                                  		'vendor_product_variant_id'     : ProductVariant.id,
			                                                               			'quantity_received'  			: line[18], 
			                                                                  		'product_uom_id'   				: CekUom[0], 
			                                                                  		'vendor_picking_id'   			: CekTampungan[3], 
			                                                                      	'vendor_product_id'     		: CekTampungan[2], 
			                                                               			'quantity'  					: line[19], 
			                                                               			'balance'  						: 0, 
			                                                                    })
												# ProductProduk.active = True
												
												# Create Product Supplier
												ProductSupplier = self.env['product.supplierinfo'].create({
			                                                                      	'vendor_product_id'     		: CekTampungan[2], 
			                                                               			'vendor_product_variant_id'   	: ProductVariant.id, 
			                                                               			'name'   						: self.partner_id.name, 
			                                                                  		'product_id'     				: BuatProduk.id,
			                                                               			'location_id'  					: Location[0], 
			                                                               			'branch_id'  					: Branch[0], 
			                                                               			'pricelist_id'  				: Pricelist[0], 
			                                                               			'delay'            				: 0,
			                                                               			'company_id'            		: 1,
			                                                               			'portal_input_price' 			: line[10], 
			                                                               			'margin_percentage' 			: CekBrand[2], 
			                                                               			'active'            			: 't',
			                                                               			'state'            				: 'draft',
			                                                                    })


												CreatePriceListItem = self.env['product.pricelist.item'].create({
			                                                                      	'applied_on'     				: '0_product_variant', 
			                                                               			'base'   						: 'list_price', 
			                                                                  		'compute_price'     			: 'fixed',
			                                                               			'pricelist_id'   				: Pricelist[0], 
			                                                               			'fixed_price'  					: line[10], 
			                                                               			'product_tmpl_id'  				: CekTampungan[1], 
			                                                                  		'product_id'     				: BuatProduk.id,
			                                                                      	'vendor_product_id'     		: CekTampungan[2], 
			                                                               			'min_quantity'  				: 0, 
			                                                               			'currency_id'            		: 12,
			                                                               			'active'            			: 't',
			                                                                    })
												
												print("+++++++++++++++++++++++++++++++ TYPE : ",line[0])
												print("+++++++++++++++++++++++++++++++ KODE : ",line[1])
												print("+++++++++++++++++++++++++++++++ PRODUK : ",BuatProduk.id)
												print("+++++++++++++++++++++++++++++++ NAME PRODUK : ",BuatProduk.name)
												print("+++++++++++++++++++++++++++++++ BARCODE : ",BuatProduk.barcode)
												
												print("============================================ TEMPLATE ID 2 : ",CekTampungan[1],)
												print("============================================ TEMPLATE ID 3 : ",BuatProduk.product_tmpl_id.id)
												print("============================================ TEMPLATE ID 4 : ",ProductSupplier.product_tmpl_id.id)
												# self.env.cr.execute(""" DELETE FROM product_template WHERE id = %s""", ( ProductProduk1.product_tmpl_id.id,))
												
												# print("======================================== ID STOCK MOVE ", CreateStokLine.id)

									else:
										raise ValidationError(('LOCATION TIDAK DITEMUKAN PADA MASTER DATA : ',line[13]))
								else:
									raise ValidationError(('PRICELIST TIDAK DITEMUKAN PADA MASTER DATA : ',line[15]))
							else:
								raise ValidationError(('BRANCH TIDAK DITEMUKAN PADA MASTER DATA : ',line[14]))
						else:
							raise ValidationError(('UNIT OF MEASURE TIDAK DITEMUKAN PADA MASTER DATA : ',line[5]))
					else:
						raise ValidationError(('KATEGORI PRODUK TIDAK DITEMUKAN PADA MASTER DATA : ',line[4]))
				else:
					raise ValidationError(('BRAND TIDAK DITEMUKAN PADA MASTER DATA : ',line[3]))

		self.env.cr.execute(""" DELETE FROM mcs_tampungan_import_do""", ())


