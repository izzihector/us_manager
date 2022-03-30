# See LICENSE file for full copyright and licensing details.
from . import models

from odoo import api, SUPERUSER_ID


def _set_default_message_template(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    pos = env["pos.config"].search([("templated_id", "=", False)])
    pos.write({"templated_id": env.ref("pos_whatsapp_connector.pos_order_status")})
