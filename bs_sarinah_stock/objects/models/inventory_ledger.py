from odoo import api, fields, models


class SetuInventoryLedgerBIReport(models.TransientModel):
    _inherit = 'setu.inventory.ledger.bi.report'

    name = fields.Char(string="Name", related='product_id.display_name', store=True)