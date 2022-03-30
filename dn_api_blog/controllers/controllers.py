# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json, base64


class DnBlogApi(http.Controller):
    @http.route('/banner_api/blog_post/<action>', type="json", auth='public')
    def blog_blog(self, limit=10, page=1, action=None,**kw):
        value = dict(kw)
        data = request.jsonrequest
        headers = request.httprequest.headers
        showTotal = False
        total_item = 0
        code = ""
        message = ""
        list_data = []
        blog_obj = request.env['blog.blog'].sudo()
        if 'Sarinah-Key' in headers:
            auth_user = request.env['ir.config_parameter'].sudo().get_param('mcs_sarinah_key')
            if headers['Sarinah-Key'] == auth_user:
                if action == 'add':
                    print('add')
                    bp = blog_obj.create({
                        # 'id': blog.id,
                        'name': data['asset_name'],
                        'subtitle': data['content_subtitle'],
                        'is_banner': True,
                        # 'image': ('http://localhost:8074/web/image/ir.attachment/%s/datas' % images.id) or None,
                    })
                    list_data.append({
                        'banner': bp.id,
                    })
                    code = "200"
                    message = "Add Success"
                elif action == 'update':
                    # if data['banner']:
                    if 'banner' in data:
                        update = request.env['blog.blog'].sudo().search([("id", "=", data['banner']),("is_banner", "=", True)])
                        if update:
                            update.write({
                                'name': data['asset_name'],
                                'subtitle': data['content_subtitle'],
                            })
                            code = "200"
                            message = "Update Success"
                        else:
                            code = "400"
                            message = "Data not found"
                    else:
                        code = "400"
                        message = "Please provide banner"
                elif action == 'delete':
                    if 'banner' in data:
                        dalete = request.env['blog.blog'].sudo().search([("id", "=", data['banner']),("is_banner", "=", True)])
                        if dalete:
                            dalete.write({
                                    'is_banner': False,
                            })
                            code = "200"
                            message = "Delete Success"
                        else:
                            code = "400"
                            message = "Data not found"
                elif action == 'list':
                    blog_blog = blog_obj.search([("is_banner", "=", True)])
                    for blog in blog_blog:
                        # images = request.env['ir.attachment'].sudo().search([('res_model','=','blog.post'),('res_field','=','pic'),('res_id','=',blog.id)])
                        # images.public = True
                        list_data.append({
                                "banner": blog.id,
                                "asset_name": blog.name,
                                "content_subtitle": blog.subtitle,
                            })
                        code = "200"
                        message = "Success"
                #     # if images:
                #     #     image = blog.pic.decode("utf-8")
                #     list_data.append({
                #         'id': blog.id,
                #         'asset_name': blog.name,
                #         'image': ('http://localhost:8074/web/image/ir.attachment/%s/datas' % images.id) or None,
                #     })
                #         # 'image': ('http://sarinahportal.co.id/web/image/ir.attachment/%s/datas' % images.id) or None,
        data = {
            "data": list_data,
            "code": code,
            "message": message,
        }

        return data
