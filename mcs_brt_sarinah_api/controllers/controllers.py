# -*- coding: utf-8 -*-
# -*- DEVELOPMENT BY : BRATA BAYU SIAHALA, S.KOM -*-
import json

from odoo import http
from odoo.http import request, _logger
from math import acos, cos, sin, radians
from odoo.addons.website_sale.controllers.main import WebsiteSale, TableCompute

from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.website.controllers.main import QueryURL
from werkzeug.exceptions import Forbidden, NotFound

from odoo.addons.web.controllers.main import ensure_db
import hashlib
from passlib.context import CryptContext
default_crypt_context = CryptContext(
    ['pbkdf2_sha512', 'md5_crypt'],
    deprecated=['md5_crypt'],
)

PPG = 20  # Products Per Page
PPR = 4  # Products Per Row

class McsBrtSarinahApi(http.Controller):

	@http.route('/product/search', auth='public', csrf=False)
	def product(self, **post):
		listdata = []
		if post.get('product_name'):
			products = request.env['product.template'].sudo().search([('name', 'ilike', str(post.get('product_name')))], limit=30)
			print("============================================ ", post.get('product_name'))
			for p in products:
				variants = []
				for x in p.product_variant_ids:
					attribute = []
					for a in x.product_template_attribute_value_ids:
						attribute.append({
													'type': a.attribute_id.name,
													'value': a.product_attribute_value_id.name,
	                              	})
						prodimage = False
						if x.image_1920:
							prodimage = x.image_1920.decode("utf-8")

						variants.append({
	                                  "id" 			: x.id,
	                                  "display_name": x.display_name,
	                                  "price" 		: x.lst_price,
	                                  "barcode" 		: x.barcode or None,
	                              	 "image" 		: prodimage or None,
	                              	 "attribute" : attribute,
	                           })

					listdata.append({
						"id": p.id,
						"name": p.name,
						"brand_id": p.brand_id.id or None,
						"brand_name": p.brand_id.name or None,
						"category_id": p.categ_id.id or None,
						"category_name": p.categ_id.display_name or None,
						"description" : p.description or None, # hs - penambahan description
						"variants": variants
					})
		else:
			listdata.append( { "Response": "Parameter Search Null!!",  } )

		data = {
                "result": listdata
            }

		jess = json.dumps(data)
		return jess


	@http.route('/brand/all', auth='public', csrf=False)
	def brandsall(self, **post):
		listdata = []
		Brands = request.env['product.brand'].sudo().search([])
		for p in Brands:
			prodimage = False
			if p.image:
				prodimage = p.image.decode("utf-8")

				listdata.append({
					"id": p.id,
					"name": p.name,
					"code": p.code,
					"total_product": p.tot_items,
               "brand_image": prodimage,
				})

		data = {
                "result": listdata
            }

		jess = json.dumps(data)
		return jess

	# @http.route('/recent/all', auth='public')
	# def recent(self):
	# 	listdata = []
	# 	Visits = request.env['website.track'].sudo().search([])
	# 	for p in Visits:
	# 		listdata.append({
	# 			"id": p.id,
	# 			"visitor_id": p.visitor_id,
	# 			"url": p.url,
	# 		})

	# 	data = {
 #                "result": listdata
 #            }

 #      jess = json.dumps(data)
	# 	return jess

	@http.route('/recent/product', auth='public', website=True)
	def recents(self):
		listdata = []
		visitor = request.env['website.visitor']._get_visitor_from_request()
		if visitor:
			excluded_products = request.website.sale_get_order().mapped('order_line.product_id.id')
			products = request.env['website.track'].sudo().read_group(
                [('visitor_id', '=', visitor.id), ('product_id', '!=', False), ('product_id.website_published', '=', True), ('product_id', 'not in', excluded_products)],
                ['product_id', 'visit_datetime:max'], ['product_id'], orderby='visit_datetime DESC')
			products_ids = [product['product_id'][0] for product in products]
			print("============================", products_ids)
			if products_ids:
				viewed_products 	= request.env['product.product'].with_context(display_default_code=False).browse(products_ids)
				FieldMonetary 		= request.env['ir.qweb.field.monetary']
				monetary_options 	= {
											'display_currency': request.website.get_current_pricelist().currency_id,
											}
				rating = request.website.viewref('website_sale.product_comment').active
				res = {'products': []}
				for p in viewed_products:
					listdata.append({
						"id": p.id,
						"name": p.name,
						"brand_id": p.brand_id.id or None,
						"brand_name": p.brand_id.name or None,
						"category_id": p.categ_id.id or None,
						"category_name": p.categ_id.display_name or None,
						"description" : p.description or None
					})
		data = {
             "result": listdata
         }

		jess = json.dumps(data)
		return jess

	@http.route('/product/populer', auth='public', csrf=False)
	def productpopuler(self, **post):
		listdata = []
		products = request.env['product.template'].sudo().search([('is_populer', '=', True)], limit=30)
		for p in products:
			variants = []
			for x in p.product_variant_ids:
				attribute = []
				for a in x.product_template_attribute_value_ids:
					attribute.append({
												'type': a.attribute_id.name,
												'value': a.product_attribute_value_id.name,
                              	})
					prodimage = False
					if x.image_1920:
						prodimage = x.image_1920.decode("utf-8")

					variants.append({
                                  "id" 			: x.id,
                                  "display_name": x.display_name,
                                  "price" 		: x.lst_price,
                                  "barcode" 		: x.barcode or None,
                              	 "image" 		: prodimage or None,
                              	 "attribute" : attribute,
                           })

				listdata.append({
					"id": p.id,
					"name": p.name,
					"brand_id": p.brand_id.id or None,
					"brand_name": p.brand_id.name or None,
					"category_id": p.categ_id.id or None,
					"category_name": p.categ_id.display_name or None,
					"description" : p.description or None, # hs - penambahan description
					"variants": variants
				})

		data = {
                "result": listdata
            }

		jess = json.dumps(data)
		return jess


	@http.route('/product/range', auth='public', csrf=False)
	def pricerange(self, **post):
		listdata = []
		if post.get('product_name'):
			products = request.env['product.template'].sudo().search([('name', 'ilike', str(post.get('product_name'))),('list_price', '>=', post.get('from_price')),('list_price', '<=', post.get('to_price'))], limit=30, order='list_price ASC')
			print("============================================ ", post.get('product_name'))
			print("============================================ ", post.get('from_price'))
			print("============================================ ", post.get('to_price'))
			for p in products:
				variants = []
				for x in p.product_variant_ids:
					attribute = []
					for a in x.product_template_attribute_value_ids:
						attribute.append({
													'type': a.attribute_id.name,
													'value': a.product_attribute_value_id.name,
	                              	})
						prodimage = False
						if x.image_1920:
							prodimage = x.image_1920.decode("utf-8")

						variants.append({
	                                  "id" 			: x.id,
	                                  "display_name": x.display_name,
	                                  "price" 		: x.lst_price,
	                                  "barcode" 		: x.barcode or None,
	                              	 "image" 		: prodimage or None,
	                              	 "attribute" : attribute,
	                           })

					listdata.append({
						"id": p.id,
						"name": p.name,
						"brand_id": p.brand_id.id or None,
						"brand_name": p.brand_id.name or None,
						"category_id": p.categ_id.id or None,
						"category_name": p.categ_id.display_name or None,
						"description" : p.description or None, # hs - penambahan description
						"variants": variants
					})
		else:
			listdata.append( { "Response": "Parameter Search Null!!",  } )

		data = {
                "result": listdata
            }

		jess = json.dumps(data)
		return jess



	@http.route('/category/level', auth='public', csrf=False)
	def levelkategori(self, **post):
		listdata = []
		if post.get('level'):
			prokate = request.env['product.category'].sudo().search(['level','=',post.get('level')])
			print("============================================ ", post.get('level'))
			for p in prokate:
				listdata.append({
					"id": p.id,
					"name": p.name,
					"complete_name": p.complete_name,
					"parent_id": p.parent_id.id,
					"parent_name": p.parent_id.name,
					"code": p.code,
					"level": p.level,
				})
		else:
			listdata.append( { "Response": "Parameter Search Null!!",  } )

		data = {
					"result": listdata
					}


		jess = json.dumps(data)
		print("====================================",data)
		return jess