# -*- coding: utf-8 -*-
##############################################################################
#
#    TL Technology
#    Copyright (C) 2019 ­TODAY TL Technology (<https://www.posodoo.com>).
#    Odoo Proprietary License v1.0 along with this program.
#
##############################################################################
from odoo import api, fields, models, tools, _, registry

import logging

_logger = logging.getLogger(__name__)

class PosSession(models.Model):
    _inherit = "pos.session"

    required_reinstall_cache = fields.Boolean('Reinstall Datas', default=0, help='If checked, when session start, all pos caches will remove and reinstall')

    def update_required_reinstall_cache(self):
        return self.write({'required_reinstall_cache': False})