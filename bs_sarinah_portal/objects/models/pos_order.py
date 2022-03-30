from odoo import api, fields, models


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    vendor_shared = fields.Float('Vendor Shared')
    discount_name = fields.Char(string="Discount Name", required=False)
    consignment_margin = fields.Float(string="Consignment Margin", compute='compute_consignment_margin', store=True)

    @api.model
    def create(self, vals):
        if vals.get('custom_discount_id'):
            discount = self.env['pos.custom.discount'].browse(vals.get('custom_discount_id'))
            if discount:
                vals.update({
                    'discount_name': discount.name,
                    'vendor_shared': discount.vendor_shared
                })
        return super(PosOrderLine, self).create(vals)

    @api.depends('product_id')
    def compute_consignment_margin(self):
        for line in self:
            if line.product_id.is_consignment:
                line.consignment_margin = line.product_id.get_current_margin()
            else:
                line.consignment_margin = 0
