from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    warehouse_ga_id = fields.Many2one(comodel_name="stock.warehouse", string="Purchase Warehouse", required=False,)




