# Copyright (C) Softhealer Technologies.

from . import models
from odoo import api, SUPERUSER_ID


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    if env.ref('sh_pos_order_list.sh_assets_js_frontend'):
        env.ref('sh_pos_order_list.sh_assets_js_frontend').write(
            {'active': False})
