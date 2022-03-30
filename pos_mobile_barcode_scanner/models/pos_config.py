# License LGPL-3.0 or later (https://www.gnu.org/licenses/Lgpl).
from odoo import api, fields, models

class PosConfig(models.Model):
    _inherit = 'pos.config'

    iface_pos_bcscanner_enable = fields.Boolean(string='Camera BarCode Snnaer', help='Enable BarCode Scanner with camera on mobile devices.')
