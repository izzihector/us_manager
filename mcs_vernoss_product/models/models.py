# -*- coding: utf-8 -*-

from odoo import models, fields, api
import requests, json
from odoo.exceptions import UserError

_BASE_URL = "http://128.199.201.196:8283"
_ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJ2ZXJub3NzIiwic3ViIjoiU0FSSUQiLCJpYXQiOjE2MzM1MzUxMjMsImV4cCI6MTY2NDk4OTIwMCwianRpIjoiMjU2M2JjZDgtZGZiOC00YjM2LWI0MzQtYWE1OTFkMDVlZjZhIn0.kQ96TeZ1JMvZYMbFWUGJM5bxCEo3M-jXSzZyMnnzTNU"
_API_KEY = "bbbc61f4-206b-48c3-a606-2ff634936efb"

class ProductCategoryVernoss(models.TransientModel):
    _name = 'product.category.vernoss'

    def send(self):
        context = dict(self._context)
        active_ids = context.get('active_ids', []) 

        for record in self.env['product.category'].browse(active_ids):
            record.send_to_vernoss()

class ProductCategory(models.Model):
    _inherit = 'product.category'

    def send_to_vernoss(self):
        error_arr = []
        for rec in self:
            headers = {
                'content-type' : "application/json",
                'Authorization' : "Bearer %s" % _ACCESS_TOKEN,
                'Api-Key' : _API_KEY,
            }

            url = "%s/loyalty/create-product-category" % _BASE_URL

            payload = {
                "categoryCode": rec.id, 
                "categoryName": rec.display_name
            }

            data = False

            try:
                res = requests.post(url, json=payload, headers=headers, verify=False)
                data = json.loads(res.content.decode('utf-8'))
            except:
                raise UserError("Failed to push categories: %s" % rec.display_name)

            if data is not False:
                if 'responseCode' in data:
                    if str(data['responseCode']) != "00":
                        error_arr.append("%s : %s" % (rec.display_name, data['responseMessage']))

        if len(error_arr) > 0:
            raise UserError('Error Vernoss: '.join(error_arr))

        return {
            'name': 'Product Category',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'product.category',
        }


class ProductVernoss(models.TransientModel):
    _name = 'product.template.vernoss'

    def send(self):
        context = dict(self._context)
        active_ids = context.get('active_ids', []) 

        for record in self.env['product.template'].browse(active_ids):
            record.send_to_vernoss()

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def send_to_vernoss(self):
        error_arr = []
        for rec in self:
            variants = rec.with_prefetch().product_variant_ids
            for variant in variants:
                headers = {
                    'content-type' : "application/json",
                    'Authorization' : "Bearer %s" % _ACCESS_TOKEN,
                    'Api-Key' : _API_KEY,
                }

                url = "%s/loyalty/create-product" % _BASE_URL

                payload = {
                    "productCode": variant.id, 
                    "productName": variant.display_name, 
                    "retailValueBeforeTax": variant.lst_price, 
                    "brandCode": variant.brand_id.id, 
                    "categoryCode": variant.categ_id.id

                }

                data = False

                try:
                    res = requests.post(url, json=payload, headers=headers, verify=False)
                    data = json.loads(res.content.decode('utf-8'))
                except:
                    raise UserError("Failed to push categories: %s" % variant.display_name)

                if data is not False:
                    if 'responseCode' in data:
                        if str(data['responseCode']) != "00":
                            error_arr.append("%s : %s" % (variant.display_name, data['responseMessage']))

        if len(error_arr) > 0:
            raise UserError('Error Vernoss: '.join(error_arr))

        return {
            'name': 'Product Category',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'product.category',
        }


class ProductProductVernoss(models.TransientModel):
    _name = 'product.product.vernoss'

    def send(self):
        context = dict(self._context)
        active_ids = context.get('active_ids', []) 

        for record in self.env['product.product'].browse(active_ids):
            record.send_to_vernoss()

class ProductProduct(models.Model):
    _inherit = 'product.product'

    def send_to_vernoss(self):
        error_arr = []
        for variant in self:
            headers = {
                'content-type' : "application/json",
                'Authorization' : "Bearer %s" % _ACCESS_TOKEN,
                'Api-Key' : _API_KEY,
            }

            url = "%s/loyalty/create-product" % _BASE_URL

            payload = {
                "productCode": variant.id, 
                "productName": variant.display_name, 
                "retailValueBeforeTax": variant.lst_price, 
                "brandCode": variant.brand_id.id, 
                "categoryCode": variant.categ_id.id

            }

            data = False

            try:
                res = requests.post(url, json=payload, headers=headers, verify=False)
                data = json.loads(res.content.decode('utf-8'))
            except:
                raise UserError("Failed to push categories: %s" % variant.display_name)

            if data is not False:
                if 'responseCode' in data:
                    if str(data['responseCode']) != "00":
                        error_arr.append("%s : %s" % (variant.display_name, data['responseMessage']))

        if len(error_arr) > 0:
            raise UserError('Error Vernoss: '.join(error_arr))

        return {
            'name': 'Product Category',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'product.category',
        }
