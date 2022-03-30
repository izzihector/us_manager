# -*- coding: utf-8 -*-

from odoo import models, fields, api


class dn_api_blog(models.Model):
    _inherit = 'blog.blog'

    is_banner = fields.Boolean('Banner')
    pic = fields.Binary('Picture', attachment=True, public=True)