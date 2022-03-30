# -*- coding: utf-8 -*-

from odoo import models, fields, api
import odoo.addons.decimal_precision as dp


class PurchaseOrderSplit(models.TransientModel):
    _name = 'purchase.order.split'
    _description = 'Split FRQ'
    
    partner_id = fields.Many2one('res.partner', string='Vendor', required=True)
    po_id = fields.Many2one('purchase.order', string='RFQ', required=True)
    date_planned = fields.Datetime('Scheduled Date', required=True)
    line_ids = fields.One2many('purchase.order.splitline', 'order_id', string='Split RFQ Line')
    
    
    def button_split(self):
        if self.ensure_one():
            poline_obj = self.env['purchase.order.line']
            new_po_id = self.po_id.copy({
                'origin': self.po_id.origin,
                'partner_id': self.partner_id.id,
                'date_order': self.date_planned,
                'date_planned': self.date_planned,
                'name': self.env['ir.sequence'].next_by_code('purchase.order'),
                'order_line': [(5, 0, 0)],
            })
            for line_id in self.line_ids:
                if line_id.po_line_int:
                    poline = poline_obj.browse(line_id.po_line_int)
                    remain_qty = poline.product_qty - line_id.split_qty
                    if line_id.split_qty > 0.0:
                        new_po_line_id = poline.copy({
                            'product_qty':line_id.split_qty,
                            'order_id':new_po_id.id,
                        })
                    if remain_qty <= 0.0:
                        poline.unlink()
                    else:
                        poline.write({'product_qty':remain_qty})
            # rfq_action = self.env['ir.actions.act_window'].browse(self.env.ref('purchase.purchase_rfq').id)
            return {
                'name': 'Splitted RFQ',
                'type': 'ir.actions.act_window',
                'target': 'current',
                'view_mode': 'tree,form',
                'src_model': 'purchase.order',
                'res_model': 'purchase.order',
                'domain': "[('id','=',%s)]" % (new_po_id.id),
                'context': {},
            }
        else:
            return False
    
    
class PurchaseOrderSplitLine(models.TransientModel):
    _name = 'purchase.order.splitline'
    _description = 'Split RFQ Line'
    
    order_id = fields.Many2one('purchase.order.split', string='Split RFQ')
    po_line_id = fields.Many2one('purchase.order.line', string='RFQ Line', readonly=True)
    product_uom = fields.Many2one('uom.uom', string='UoM', related='po_line_id.product_uom', readonly=True)
    product_qty = fields.Float(string='RFQ Qty', digits='Product Unit of Measure', related='po_line_id.product_qty', readonly=True)
    
    split_qty = fields.Float(string='Split Qty', digits='Product Unit of Measure', required=True)
    base_qty = fields.Float(string='Base Qty', digits='Product Unit of Measure', required=True)
    po_line_int = fields.Integer('RFQ Line Integer', required=True)
    
    _sql_constraints = [
        ('check_split_qty_product_qty', 'CHECK(split_qty<=base_qty)', 'Split Qty must not be greater than Product Qty.'),
        ('check_split_qty', 'CHECK(split_qty>0)', 'Split Qty must be greater than 0.'),
    ]
