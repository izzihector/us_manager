from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.misc import clean_context, DEFAULT_SERVER_DATE_FORMAT


class ProductReplenishRequest(models.Model):
    _inherit = 'product.replenish.request'

    def launch_replenishment(self):
        if not self.replenish_request_id.is_ga:
            return super(ProductReplenishRequest, self).launch_replenishment()
        else:
            if self.ensure_one():
                uom_reference = self.product_id.uom_id
                warehouse = self.company_id.sudo().warehouse_ga_id
                self.write({
                    'quantity':self.product_uom_id._compute_quantity(self.quantity, uom_reference),
                    'confirm_uid':self.env.user.id,
                })
                try:
                    values = self._prepare_run_values()
                    self.env['procurement.group'].sudo().with_context(clean_context(self.env.context)).run([self.env['procurement.group'].Procurement(
                        self.product_id,
                        self.quantity,
                        uom_reference,
                        warehouse.lot_stock_id,
                        values['group_id'].name,  # Name
                        values['group_id'].name,  # Origin
                        self.env.company,
                        values  # Values
                    )])

                    self.state = 'confirm'
                    if self.replenish_request_id:
                        part_confirm = False
                        for product in self.replenish_request_id.product_replenish_ids:
                            if product.state == 'draft':
                                part_confirm = True
                        self.replenish_request_id.write({
                            'confirm_uid':self.env.user.id,
                            'state':'part_confirm' if part_confirm else 'confirm'
                        })
                except UserError as error:
                    raise UserError(error)
            return True

    def _prepare_run_values(self):
        if not self.replenish_request_id.is_ga:
            return super(ProductReplenishRequest, self)._prepare_run_values()
        else:
            if self.state != 'approve':
                raise UserError('Request already confirmed')
            self.group_id = self.env['procurement.group'].create({
                'partner_id': self.product_id.responsible_id.partner_id.id,
            })
            values = {
                'warehouse_id': self.company_id.warehouse_ga_id,
                'route_ids': self.route_ids,
                'date_planned': self.date_planned or fields.Datetime.now(),
                'group_id': self.group_id,
            }
            return values

