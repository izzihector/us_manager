from odoo import api, fields, models 


class WizardVendorStockPicking(models.TransientModel):
    _name = 'wizard.vendor.stock.picking'
    _description = 'Vendor Stock Picking Wizard'

    picking_id = fields.Many2one(comodel_name='vendor.stock.picking', string='Vendor Stock Picking', required=True)
    move_ids = fields.One2many(comodel_name='vendor.stock.move', string='Moves', related='picking_id.vendor_move_ids')
    is_received_empty = fields.Boolean(string='Received is Empty', compute='_compute_picking_status')
    is_fully_received = fields.Boolean(string='Fully Received', compute='_compute_picking_status')

    @api.depends('move_ids.quantity_received')
    def _compute_picking_status(self):
        for record in self:
            move_ids = record.picking_id.vendor_move_ids
            record.is_received_empty = all((move.quantity_received == 0 for move in move_ids))
            record.is_fully_received = all((move.quantity_received == move.quantity for move in move_ids))

    def fill_and_validate(self):
        for record in self:
            for move in record.move_ids:
                move.quantity_received = move.quantity
        self.validate()

    def validate(self):
        for record in self:
            record.picking_id.with_context({
                'active_id': record.picking_id.id
            }).action_validate()
