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

		# LLHa 2022-02-08
		user_warning = ""

		Warna = self.env['product.attribute'].sudo().search([('name', '=', 'Warna / Jenis')], limit=1)
		if not Warna:
			user_warning += "\nTidak ada master data attribute dengan nama 'Warna / Jenis'"

		Model = self.env['product.attribute'].sudo().search([('name', '=', 'Model')], limit=1)
		if not Model:
			user_warning += "\nTidak ada master data attribute dengan nama 'Model'"

		Motif = self.env['product.attribute'].sudo().search([('name', '=', 'Motif')], limit=1)
		if not Motif:
			user_warning += "\nTidak ada master data attribute dengan nama 'Motif'"

		Size = self.env['product.attribute'].sudo().search([('name', '=', 'Size')], limit=1)
		if not Size:
			user_warning += "\nTidak ada master data attribute dengan nama 'Size'"

		Tema = self.env['product.attribute'].sudo().search([('name', '=', 'Tema / Season')], limit=1)
		if not Tema:
			user_warning += "\nTidak ada master data attribute dengan nama 'Tema / Season'"

		Bahan = self.env['product.attribute'].sudo().search([('name', '=', 'Bahan')], limit=1)
		if not Bahan:
			user_warning += "\nTidak ada master data attribute dengan nama 'Bahan'"

		if user_warning:
			raise ValidationError(('Error: ', user_warning))

		user_warning = ""
		for row_no in range(sheet.nrows):
			if row_no > 0:
				line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value),sheet.row(row_no)))

				CekBrand = self.env['product.brand'].sudo().search([('name', '=', line[3])],limit=1)
				if not CekBrand:
					user_warning += '\nBRAND TIDAK DITEMUKAN PADA MASTER DATA : %s (row %s)' % (line[3], row_no+1)
				else:
					if CekBrand not in self.partner_id.brand_ids:
						user_warning += '\nBRAND TIDAK ADA DI VENDOR INI : %s (row %s)' % (line[3], row_no + 1)

				CekKategori = self.env['product.category'].sudo().search([('complete_name', '=', line[4])], limit=1)
				if not CekKategori:
					user_warning += '\nKATEGORI PRODUK TIDAK DITEMUKAN PADA MASTER DATA : %s (row %s)' % (line[4], row_no+1)

				CekUom = self.env['uom.uom'].sudo().search([('name', '=', line[5])], limit=1)
				if not CekUom:
					user_warning += '\nUNIT OF MEASURE TIDAK DITEMUKAN PADA MASTER DATA : %s (row %s)' % (line[5], row_no+1)

				Branch = self.env['res.branch'].sudo().search([('name', '=', line[8])], limit=1)
				if not Branch:
					user_warning += '\nBRANCH TIDAK DITEMUKAN PADA MASTER DATA : %s (row %s)' % (line[8], row_no+1)

				Pricelist = self.env['product.pricelist'].sudo().search([('name', '=', line[9])], limit=1)
				if not Pricelist:
					user_warning += '\nPRICELIST TIDAK DITEMUKAN PADA MASTER DATA : %s (row %s)' % (line[9], row_no+1)

				Location = self.env['vendor.location'].sudo().search([('name', '=', line[7])], limit=1)
				if not Location:
					user_warning += '\nLOCATION TIDAK DITEMUKAN PADA MASTER DATA : %s (row %s)' % (line[7], row_no+1)

				if line[11]:
					CekWarna = self.env['product.attribute.value'].sudo().search([('name', '=', line[11]),
																				   ('attribute_id', '=', Warna.id)],
																				 limit=1)
					if not CekWarna:
						user_warning += '\nWARNA TIDAK DITEMUKAN PADA MASTER DATA : %s (row %s)' % (line[11], row_no + 1)

				if line[12]:
					CekSize = self.env['product.attribute.value'].sudo().search([('name', '=', line[12].replace(".0", "")),
																				   ('attribute_id', '=', Size.id)],
																				limit=1)
					if not CekSize:
						user_warning += '\nSIZE TIDAK DITEMUKAN PADA MASTER DATA : %s (row %s)' % (line[12], row_no + 1)

				if line[13]:
					CekModel = self.env['product.attribute.value'].sudo().search([('name', '=', line[13]),
																				   ('attribute_id', '=', Model.id)], limit=1)
					if not CekModel:
						user_warning += '\nModel TIDAK DITEMUKAN PADA MASTER DATA : %s (row %s)' % (line[13], row_no + 1)

				if line[14]:
					CekTema = self.env['product.attribute.value'].sudo().search([('name', '=', line[14]),
																				   ('attribute_id', '=', Tema.id)], limit=1)
					if not CekTema:
						user_warning += '\nTema TIDAK DITEMUKAN PADA MASTER DATA : %s (row %s)' % (line[14], row_no + 1)

				if line[15]:
					CekMotif = self.env['product.attribute.value'].sudo().search([('name', '=', line[15]),
																				   ('attribute_id', '=', Motif.id)], limit=1)
					if not CekMotif:
						user_warning += '\nMotif TIDAK DITEMUKAN PADA MASTER DATA : %s (row %s)' % (line[15], row_no + 1)

				if line[16]:
					CekBahan = self.env['product.attribute.value'].sudo().search([('name', '=', line[16]),
																				   ('attribute_id', '=', Bahan.id)], limit=1)
					if not CekBahan:
						user_warning += '\nBahan TIDAK DITEMUKAN PADA MASTER DATA : %s (row %s)' % (line[16], row_no + 1)

		if user_warning:
			raise ValidationError(('Error: %s' % user_warning))

		# !LLHa 2022-02-08

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
											CreateProductTemplate = self.env['product.template'].sudo().create({
																				'name'              	: line[2],
			                                                                  	'sale_ok'        		: 't',
			                                                                  	'is_consignment'  		: 't',
			                                                                  	'is_autonaming'  		: 't',
			                                                                  	'is_published'  		: 't',
			                                                                  	'available_in_pos'  	: 'f',
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
			                                                                  	'active'            	: 't',
			                                                                  	'purchase_line_warn'	: 'no-message'
																									})

											# create produk vendor
											CreateProductVendor = self.env['vendor.product'].sudo().create({
			                                                                  	'product_name'          : line[2],
			                                                                  	'margin_percentage'     : CekBrand.consignment_margin,
			                                                                  	'partner_id'        	: self.partner_id.id,
			                                                                  	'product_category_id'	: CekKategori.id,
			                                                                  	'product_uom_id'   		: CekUom.id,
			                                                                  	'product_brand_id'   	: CekBrand.id,
			                                                                  	'product_tmpl_id'    	: CreateProductTemplate.id,
			                                                                  	'company_id'            : 1,
			                                                                  	'state'        			: line[6],
			                                                                  	'active'            	: 't'
			                                                                })

											CreateProductTemplate.default_code = CreateProductVendor.product_code
											CreateProductTemplate.active = True

											prdprd = self.env['product.product'].sudo().search([('product_tmpl_id', '=', CreateProductTemplate.id)],limit=1)
											self.env.cr.execute(""" DELETE FROM product_product WHERE id = %s""", ( prdprd.id,))


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
												'vendor_location_id'	: Location.id,
												'operation_type'  		: 'incoming',
												'state'  				: 'draft',
											})
											kode = str(line[1].replace(".0", ""))
											# create tampungan
											Createtampungan = self.env['mcs.tampungan.import.do'].create({
												'name'              	: 'Data Import',
												'kode'					: int(kode),
												'id_do' 				: CreateHeaderDo.id,
												'product_tmpl_id' 		: CreateProductTemplate.id,
												'vendor_product_id'  	: CreateProductVendor.id,
												'partner_id'  			: self.partner_id.id,
												'brand_id'  			: CekBrand.id,
												'location_id'  			: Location.id,
												'branch_id'  			: Branch.id,
												'pricelist_id'  		: Pricelist.id,
												'portal_input_price' 	: line[10],
												'margin_percentage'  	: CekBrand.consignment_margin,
											})


											print("============================================ TEMPLATE ID 1 : ",CreateProductTemplate.id,)
										elif line[0] == 'Variant':
											kode = str(line[1].replace(".0", ""))
											CekTampungan = self.env['mcs.tampungan.import.do'].sudo().search([('kode', '=', int(kode))],limit=1)
											if CekTampungan:

												# CREATE PRODUK VARIANT
												BuatProduk = self.env['product.product'].sudo().create({
													'product_tmpl_id'    	: CekTampungan.product_tmpl_id.id,
													'company_id'            : 1,
													'brand_id'  			: CekBrand.id,
													# 'combination_indices'	: 1,
												})

												BuatProduk.combination_indices 	= CekTampungan.id
												# Create Product Varian
												ProductVariant = self.env['vendor.product.variant'].sudo().create({
													'partner_id'        	: self.partner_id.id,
													'vendor_product_id'     : CekTampungan.vendor_product_id.id,
													'product_name'          : line[2],
													'product_id'     		: BuatProduk.id,
													'product_tmpl_id'    	: CekTampungan.product_tmpl_id.id,
													'company_id'            : 1,
													'active'            	: 't',
												})



												CekWarna = self.env['product.attribute.value'].sudo().search([('name', '=', line[11])],limit=1)
												if CekWarna:
													# warna ada
													ProductVariant.attribute_value_ids 	=  [(4, CekWarna.id)]

													CekAttributLine = self.env['vendor.product.attr.line'].sudo().search([('vendor_product_id', '=', CekTampungan.vendor_product_id.id),('attribute_id', '=', 1)],limit=1)
													ValueWarna = self.env['product.attribute.value'].sudo().search([('name', '=', line[11].replace(".0", ""))],limit=1)
													if CekAttributLine:
														# jika atribute ada maka di edit untk nambahkan value di attribute yg sama
														# edit variant yg ada
														CekAttributLine.value_ids = [(4, ValueWarna.id)]

													else:
														# cek atribut utk create varian
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
													ValueSize = self.env['product.attribute.value'].sudo().search([('name', '=', line[12].replace(".0", ""))],limit=1)
													if CekAttributLine:
														# jika atribute ada maka di edit untk nambahkan value di attribute yg sama
														# edit variant yg ada
														CekAttributLine.value_ids = [(4, ValueSize.id)]

													else:
														# cek atribut utk create varian
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

												CreateStokLine = self.env['vendor.stock.move'].create({
													'name'     						: line[2],
													'partner_id'   					: self.partner_id.id,
													'vendor_product_variant_id'     : ProductVariant.id,
													'quantity_received'  			: line[18],
													'product_uom_id'   				: CekUom.id,
													'vendor_picking_id'   			: CekTampungan.id_do.id,
													'vendor_product_id'     		: CekTampungan.vendor_product_id.id,
													'quantity'  					: line[19],
													'balance'  						: 0,
												})
												# ProductProduk.active = True

												# Create Product Supplier
												ProductSupplier = self.env['product.supplierinfo'].create({
													'vendor_product_id'     		: CekTampungan.vendor_product_id.id,
													'vendor_product_variant_id'   	: ProductVariant.id,
													'name'   						: self.partner_id.name,
													'product_id'     				: BuatProduk.id,
													'location_id'  					: Location.id,
													'branch_id'  					: Branch.id,
													'pricelist_id'  				: Pricelist.id,
													'delay'            				: 0,
													'company_id'            		: 1,
													'portal_input_price' 			: line[10],
													'margin_percentage' 			: CekBrand.consignment_margin,
													'active'            			: 't',
													'state'            				: 'draft',
												})


												CreatePriceListItem = self.env['product.pricelist.item'].create({
													'applied_on'     				: '0_product_variant',
													'base'   						: 'list_price',
													'compute_price'     			: 'fixed',
													'pricelist_id'   				: Pricelist.id,
													'fixed_price'  					: line[10],
													'product_tmpl_id'  				: CekTampungan.product_tmpl_id.id,
													'product_id'     				: BuatProduk.id,
													'vendor_product_id'     		: CekTampungan.vendor_product_id.id,
													'min_quantity'  				: 0,
													'currency_id'            		: 12,
													'active'            			: 't',
												})

												print("+++++++++++++++++++++++++++++++ TYPE : ",line[0])
												print("+++++++++++++++++++++++++++++++ KODE : ",line[1])
												print("+++++++++++++++++++++++++++++++ PRODUK : ",BuatProduk.id)
												print("+++++++++++++++++++++++++++++++ NAME PRODUK : ",BuatProduk.name)
												print("+++++++++++++++++++++++++++++++ BARCODE : ",BuatProduk.barcode)

												print("============================================ TEMPLATE ID 2 : ",CekTampungan.product_tmpl_id.id,)
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


