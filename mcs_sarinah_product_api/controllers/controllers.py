# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json
import math
import logging
_logger = logging.getLogger(__name__)

class McsSarinahProductApi(http.Controller):
    @http.route('/sarinah/delete_product_product', auth='public')
    def delete_product(self, **kw):
        ids = [3180,3182,2716,2718,2720,2722,6200,8353,1775,1776,1777,3541,3542,3543,3544,8420,8419,3906,4413,6173,6174,7687,2668,2396,2400,8113,8114,8115,8117,8118,8424,8107,8108,8400,8111,8112,8407,8542,2038,2632,5032,5033,5034,5055,5056,5057,5058,5059,5060,5061,5042,5043,5044,5045,5066,5067,5048,5069,5070,5071,4239,4240,4241,4242,5177,5179,5183,5184,5185,5447,5448,5449,5450,5451,5452,5453,5454,5455,5456,5457,5458,6584,6585,6586,6915,6917,6918,6971,6950,6951,6955,6960,6961,6962,6963,6967,6969,8386]
        to_deletes = request.env['product.product'].sudo().search([('id', 'in', ids)])
        
        listdata = []
        for to_delete in to_deletes:
            # to_delete.unlink()
            listdata.append({
                "id": to_delete.id, 
                "name": to_delete.name,
            })
        
        data = {
            "result": listdata,
            "total": len(listdata),
        }

        jess = json.dumps(data)
        return jess

    @http.route('/sarinah/generate_pricelist', auth='public')
    def generate_pricelist(self, **kw):
        ids = [7411,7412,7413,7414,7415,7416,7417,7418,7419,7420,7421,7422,7423,7424,7425,7426,7427,7428,7429,7430,7431,7432,7433,7434,7435,7436,7437,7438,7439,7440,7441,7442,7443,7444,7445,7446,7447,7448,7449,7450,7451,7452,7453,7454,7455,7456,7457,7458,7459,7460,7461,7462,7463,7464,7465,7466,7467,7468,7469,7470,7471,7472,7473,7474,7475,7476,7477,7478,7479,7480,7481,7482,7483,7484,7485,7486,7487,7488,7489,7490,7491,7492,7493,7494,7495,7496,7497,7498,7499,7500,7501,7502,7503,7504,7505,7506,7507,7508,7509,7510,7511,7512,7513,7514,7515,7516,7517,7518,7519,7520,7521,7522,7523,7524,7525,7526,7527,7528,7529,7530,7531,7532,7533,7534,7535,7536,7537,7538,7539,7540,7541,7542,7543,7544,7545,7546,7547,7548,7549,7550,7551,7552,7553,7554,7555,7556,7557,7558,7559]
        to_deletes = request.env['product.pricelist.item'].sudo().search([('id', 'in', ids)])
        for to_delete in to_deletes:
            to_delete.unlink()

        product_products = request.env['product.product'].sudo().search([('is_consignment', '=', False)])

        listdata = []
        for product_product in product_products:
            pricelist = request.env['product.pricelist.item'].sudo().search([('product_id', '=', product_product.id)])
            if len(pricelist) < 1 and product_product.lst_price > 0: 
                hasPriceTemp = request.env['product.pricelist.item'].sudo().search([('product_id', '=', False), ('product_tmpl_id', '=', product_product.product_tmpl_id.id)])

                if not hasPriceTemp:
                    res = request.env['product.pricelist.item'].sudo().create({
                        'pricelist_id': 1,
                        'product_id': product_product.id,
                        # 'product_tmpl_id': product_product.product_tmpl_id.id,
                        'fixed_price' : product_product.lst_price,
                        'applied_on': '0_product_variant',
                        'base': 'list_price',
                        'compute_price': 'fixed',
                        'min_quantity': 0,
                        'active': 't',
                    })
                    if res:
                        listdata.append({
                            "sku_id": res.id,
                            "product_id": product_product.id,
                            "product_name": product_product.name,
                            "sku_price": product_product.lst_price,
                            "product_tmpl_id": product_product.product_tmpl_id.id,
                        })
        
        data = {
            "result": listdata,
            "total": len(listdata),
        }

        jess = json.dumps(data)
        return jess
        
    @http.route('/sarinah/<string:data>/<string:option>', auth='public')
    def product(self, limit=10, page=1, **kw):
        value = dict(kw)
        data = value['data']
        headers = request.httprequest.headers
        listdata = []
        showTotal = False
        total_item = 0

        if 'Sarinah-Key' in headers:
            auth_user = request.env['ir.config_parameter'].sudo().get_param('mcs_sarinah_key')
            if headers['Sarinah-Key'] == auth_user:

                if data == 'product':
                    categories = [302]  # id sealable

                    categories_ids = request.env['product.category'].sudo().search([('parent_id', 'child_of', categories)])
                    if categories_ids:
                        for c in categories_ids:
                            if c.id not in categories:
                                categories.append(c.id)

                    if str(limit).isdigit():
                        _limit = int(limit)
                    else:
                        _limit = 10

                    if str(page).isdigit():
                        _page = int(page) - 1
                        if _page < 0:
                            _page = 0
                        _offset = _page * _limit
                    else:
                        _offset = 0

                    if _limit < 0:
                        _limit = 10
                    if _offset < 0:
                        _offset = 0 

                    options = value['option']
                    options = options.split('-')
                    option = options[0]
                    categ_id = None
                    if len(options) > 1:
                        if options[1].isdigit():
                            categ_id = int(options[1])
                        else:
                            categ_id = 'False'
                            listdata.append(
                                {
                                    "Response": "Please provide correct id for category! e.g. category-1",
                                }
                            )
                    print(type(option) == int)
                    if option == 'all':
                        products = request.env['product.template'].sudo().search([('categ_id', 'in', categories)], limit=_limit, offset=_offset)

                        showTotal = True
                        total_item = request.env['product.template'].sudo().search_count([('categ_id', 'in', categories)])

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
                                        "id": x.id,
                                        "display_name": x.display_name,
                                        "price": x.lst_price,
                                        "barcode": x.barcode or None,
                                        "image": prodimage or None,
                                        "attribute": attribute,
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
                    elif option.isdigit():
                        products = request.env['product.template'].sudo().search([('id', '=', option)])

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
                                    "id": x.id,
                                    "display_name": x.display_name,
                                    "price": x.lst_price,
                                    "barcode": x.barcode or None,
                                    "image": prodimage or None,
                                    "attribute": attribute,
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
                    elif option == 'category':
                        if categ_id:
                            if categ_id != 'False':
                                product_template = request.env['product.template'].sudo().search([('categ_id', '=', categ_id)], limit=_limit, offset=_offset)

                                for p in product_template:
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
                                            "id": x.id,
                                            "display_name": x.display_name,
                                            "price": x.lst_price,
                                            "barcode": x.barcode or None,
                                            "image": prodimage or None,
                                            "attribute": attribute,
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
                                products = []
                        else:
                            products = request.env['product.category'].sudo().search([('id', 'in', categories)], limit=_limit, offset=_offset)

                            for x in products:
                                listdata.append(
                                    {
                                        "id": x.id,
                                        "name": x.name,
                                        "display_name": x.display_name,
                                    }
                                )
                    elif option == 'brand':
                        showTotal = True
                        if categ_id:
                            if categ_id != 'False':
                                product_template = request.env['product.template'].sudo().search([('categ_id', 'in', categories), ('brand_id', '=', categ_id)], limit=_limit, offset=_offset)
                                total_item = request.env['product.template'].sudo().search_count([('categ_id', 'in', categories), ('brand_id', '=', categ_id)])
                                
                                for p in product_template:
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
                                            "id": x.id,
                                            "display_name": x.display_name,
                                            "price": x.lst_price,
                                            "barcode": x.barcode or None,
                                            "image": prodimage or None,
                                            "attribute": attribute,
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
                                products = []
                        else:
                            products = request.env['product.brand'].sudo().search([], limit=_limit, offset=_offset)
                            total_item = request.env['product.brand'].sudo().search_count([])

                            for x in products:
                                listdata.append(
                                    {
                                        "id": x.id,
                                        "name": x.name,
                                    }
                                )
                    elif option == 'delete':
                        if categ_id:
                            if categ_id != 'False':
                                product_template = request.env['product.template'].sudo().search([('id', '=', categ_id)])

                                for x in product_template:
                                    x.active = False

                                if len(product_template) > 0:
                                    listdata.append(
                                        {
                                            "Response": "Successfully delete product %s" % categ_id,
                                        }
                                    )
                                else:
                                    listdata.append(
                                        {
                                            "Response": "Product %s not found" % categ_id,
                                        }
                                    )
                            else:
                                listdata.append(
                                    {
                                        "Response": "Please provide valid endpoint!",
                                    }
                                )
                        else:
                            listdata.append(
                                {
                                    "Response": "Please provide valid endpoint!",
                                }
                            )
                    else:
                        listdata.append(
                            {
                                "Response": "Please provide valid endpoint!",
                            }
                        )

                elif data == 'contact':
                    contact = request.env['res.partner'].sudo().search([('is_merchant', '=', True)])
                    for x in contact:
                        listdata.append(
                            {
                                "id": x.id,
                                "name": x.name,
                            }
                        )
                else:
                    listdata.append(
                        {
                            "Response": "Please provide valid endpoint!",
                        }
                    )
            else:
                listdata.append(
                    {
                        "Response": "Invalid Key!",
                    }
                )
        else:
            listdata.append(
                {
                    "Response": "Please provide valid key in headers!",
                }
            )

        if showTotal == True:
            data = {
                "result": listdata,
                "current_page": page,
                "total_page": int(math.ceil(int(total_item) / int(limit))),
                "total_item": total_item,
            }
        else:
            data = {
                "result": listdata
            }

        jess = json.dumps(data)
        return jess
