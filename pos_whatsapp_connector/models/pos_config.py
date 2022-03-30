# See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models


class PosConfig(models.Model):
    """Inherit Pos Config."""

    _inherit = "pos.config"

    def _default_pos_msg_template_id(self):
        templated_id = self.env.ref(
            "pos_whatsapp_connector.pos_order_status", raise_if_not_found=False
        )
        return templated_id and templated_id.id

    is_send_whatsapp = fields.Boolean(string="Send Receipt Via Whatsapp")
    templated_id = fields.Many2one(
        "mail.template",
        string="Message Template",
        domain="[('is_whatsapp', '=', True), ('model_id', '=', 'pos.order')]",
        default=lambda self: self._default_pos_msg_template_id(),
    )
