# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class WizardConsignmentBills(models.TransientModel):
    _name = 'wizard.consignment.bills'
    _description = 'Wizard Consignment Bills'

    branch_ids = fields.Many2many(comodel_name="res.branch", string="Branch(s)")
    partner_id = fields.Many2one(comodel_name="res.partner", string="Vendor", required=True)
    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)
    price_total = fields.Float(string="Total", compute='compute_price_total')
    price_subtotal = fields.Float(string="Total Untaxed", compute='compute_price_total')
    company_id = fields.Many2one(comodel_name="res.company", string="Company",
                                  default=lambda self: self.env.user.company_id)
    currency_id = fields.Many2one(comodel_name="res.currency", string="Currency",
                                  default=lambda self: self.env.user.company_id.currency_id)
    line_ids = fields.One2many(comodel_name="wizard.consignment.bills.line", inverse_name="wizard_id",
                               string="Details", required=False)

    @api.onchange('line_ids')
    def compute_price_total(self):
        self.price_total = sum(self.line_ids.mapped('total'))
        self.price_subtotal = sum(self.line_ids.mapped('subtotal'))

    @api.onchange('start_date', 'end_date', 'partner_id', 'branch_ids')
    def compute_line_ids(self):
        # clear the relation, because there is a problem if I delete the lines record
        self.line_ids.write({'wizard_id': False})
        if self.partner_id and self.start_date and self.end_date and self.branch_ids:
            line_obj = self.env['wizard.consignment.bills.line']
            # order from sales order
            sale_domain = [('order_id.date_order', '>=', self.start_date),
                           ('order_id.date_order', '<=', self.end_date),
                           ('qty_delivered', '>', 0),
                           ('order_id.branch_id', 'in', self.branch_ids.ids),
                           ('product_owner_id', '=', self.partner_id.id),
                           ('consignment_invoice_state', 'not in', ['draft', 'posted'])]
            sale_lines = self.env['sale.order.line'].search(sale_domain)
            for branch in self.branch_ids:
                branch_sales = sale_lines.filtered(lambda l: l.order_id.branch_id == branch._origin)
                partners = branch_sales.mapped('product_owner_id')
                for partner in partners:
                    partner_sales = branch_sales.filtered(lambda l: l.product_owner_id == partner)
                    products = partner_sales.mapped('product_id')
                    for product in products:
                        product_sales = partner_sales.filtered(lambda l: l.product_id == product)
                        unit_prices = product_sales.mapped('price_unit')
                        for price in list(set(unit_prices)):
                            price_sales = product_sales.filtered(lambda l: l.price_unit == price)
                            if price_sales:
                                price_unit_wo_tax = sum(price_sales.mapped('price_subtotal')) / sum(
                                    price_sales.mapped('product_uom_qty'))
                                vendor_product = self.env['vendor.product.variant'].sudo().search(
                                    [('product_id', '=', product.id)])
                                if vendor_product:
                                    margin = vendor_product.margin_percentage
                                else:
                                    margin = product.owner_id.consignment_margin
                                price_after_margin = price_unit_wo_tax * ((100 - margin) / 100)
                                total_qty = sum(price_sales.mapped('qty_delivered'))
                                line_obj.create({
                                    'wizard_id': self.id,
                                    'branch_id': branch._origin.id,
                                    'department_id': branch.department_id.id,
                                    'partner_id': partner.id,
                                    'product_id': product.id,
                                    'price_unit': price_after_margin,
                                    'sale_price': price,
                                    'product_qty': total_qty,
                                    'product_uom_id': product.uom_id.id,
                                    'sale_line_ids': price_sales.ids
                                })
            # order from pos order
            pos_domain = [('order_id.date_order', '>=', self.start_date),
                          ('order_id.date_order', '<=', self.end_date),
                          ('order_id.config_id.branch_id', 'in', self.branch_ids.ids),
                          ('product_owner_id', '=', self.partner_id.id),
                          ('consignment_invoice_state', 'not in', ['draft', 'posted'])]
            pos_lines = self.env['pos.order.line'].search(pos_domain)
            for branch in self.branch_ids:
                branch_sales = pos_lines.filtered(lambda l: l.order_id.config_id.branch_id == branch._origin)
                partners = branch_sales.mapped('product_owner_id')
                for partner in partners:
                    partner_sales = branch_sales.filtered(lambda l: l.product_owner_id == partner)
                    products = partner_sales.mapped('product_id')
                    for product in products:
                        product_sales = partner_sales.filtered(lambda l: l.product_id == product)
                        cons_margins = list(set(product_sales.mapped('consignment_margin')))
                        for margin in cons_margins:
                            margin_price = product_sales.filtered(lambda l: l.consignment_margin == margin)
                            unit_prices = margin_price.mapped('price_unit')
                            for price in list(set(unit_prices)):
                                price_sales = product_sales.filtered(lambda l: l.price_unit == price)
                                vendor_shares = list(set(price_sales.mapped('vendor_shared')))
                                for share in vendor_shares:
                                    shared_lines = price_sales.filtered(lambda l: l.vendor_shared == share)
                                    subtotal = 0
                                    for line in shared_lines:
                                        subtotal += line.price_unit * line.qty
                                    vendor_margin = 100 - margin
                                    vendor_margin_amount = vendor_margin / 110 * subtotal
                                    discount = 0
                                    for line in shared_lines:
                                        discount += line.price_unit * line.qty * line.discount / 100 + line.fix_discount
                                    vendor_shared = share
                                    vendor_shared_amount = vendor_shared / 110 * discount
                                    total_qty = sum(shared_lines.mapped('qty'))
                                    price_unit = (vendor_margin_amount - vendor_shared_amount) / total_qty
                                    line_obj.create({
                                        'wizard_id': self.id,
                                        'branch_id': branch._origin.id,
                                        'department_id': branch.department_id.id,
                                        'partner_id': partner.id,
                                        'product_id': product.id,
                                        'price_unit': price_unit,
                                        'sale_price': price,
                                        'product_qty': total_qty,
                                        'product_uom_id': product.uom_id.id,
                                        'pos_line_ids': price_sales.ids
                                    })

    def create_bills(self):
        if not self.line_ids:
            raise ValidationError("Sorry you cannot create empty bills.")
        bill_obj = self.env['account.move']
        branchs = self.line_ids.mapped('branch_id')
        bills = []
        for branch in branchs:
            branch_lines = self.line_ids.filtered(lambda l: l.branch_id.id == branch.id)
            partners = branch_lines.mapped('partner_id')
            for partner in partners:
                new_lines = self.env['account.move.line']
                bill = bill_obj.with_context({'check_move_validity': False}).create({
                    'partner_id': partner.id,
                    'type': 'in_invoice',
                    'branch_id': branch.id,
                    'department_id': branch.department_id.id,
                    'currency_id': self.currency_id.id,
                    'consignment_date_start': self.start_date,
                    'consignment_date_end': self.end_date,
                    'is_consignment': True
                })
                partner_lines = branch_lines.filtered(lambda l: l.partner_id == partner)
                subtotal = sum(partner_lines.mapped('subtotal'))
                for line in branch_lines.filtered(lambda l: l.partner_id == partner):
                    # accounts = line.product_id.product_tmpl_id.get_product_accounts()
                    account = line.department_id.account_stock_output_consign_id or \
                              line.product_id.product_tmpl_id.get_product_accounts()['expense']
                    vals = {
                        'name': line.product_id.display_name,
                        'move_id': bill.id,
                        'product_uom_id': line.product_uom_id.id,
                        'product_id': line.product_id.id,
                        'price_unit': line.price_unit,
                        'quantity': line.product_qty,
                        'partner_id': bill.partner_id.id,
                        'account_id': account.id,
                        'tax_ids': line.tax_ids.ids,
                    }
                    if subtotal >= self.company_id.auto_add_tax_amount:
                        tax = self.company_id.consignment_tax_id
                        if not tax:
                            raise ValidationError("Please set consignment bills taxes in accounting configurations before process this operations!")
                        vals.update({
                            'tax_ids': vals['tax_ids'] + tax.ids
                        })
                    if subtotal >= self.company_id.auto_add_second_tax_amount:
                        tax = self.company_id.consignment_second_tax_id
                        if not tax:
                            raise ValidationError("Please set consignment bills taxes in accounting configurations before process this operations!")
                        vals.update({
                            'tax_ids': vals['tax_ids'] + tax.ids
                        })
                    new_line = new_lines.with_context({'check_move_validity': False}).create(vals)
                    new_line._onchange_price_subtotal()
                    line.sale_line_ids.write({
                        'consignment_invoice_id': new_line.id
                    })
                    line.pos_line_ids.write({
                        'consignment_invoice_id': new_line.id
                    })
                    new_lines += new_line
                bill.with_context({'check_move_validity': False}).write({'invoice_line_ids': new_lines.ids})
                bills.append(bill.id)
            # new_lines._onchange_mark_recompute_taxes()

        # action view bills
        action = self.env.ref('account.action_move_in_invoice_type')
        result = action.read()[0]
        if len(bills) > 1:
            result['domain'] = "[('id', 'in', " + str(bills) + ")]"
        else:
            res = self.env.ref('account.view_move_form', False)
            form_view = [(res and res.id or False, 'form')]
            if 'views' in result:
                result['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                result['views'] = form_view
            result['res_id'] = bills[0] or False
        return result


class WizardConsignmentBillsLine(models.TransientModel):
    _name = 'wizard.consignment.bills.line'
    _description = 'Wizard Consignment Bills Line'

    wizard_id = fields.Many2one(comodel_name="wizard.consignment.bills", string="Wizard")
    department_id = fields.Many2one(comodel_name="hr.department", string="Department", required=True)
    partner_id = fields.Many2one(comodel_name="res.partner", string="Vendor", required=True)
    product_id = fields.Many2one(comodel_name="product.product", string="Product", required=True)
    product_uom_id = fields.Many2one(comodel_name="uom.uom", string="UoM", required=True)
    product_qty = fields.Float(string="Quantity", required=True, digits='Product Unit of Measure')
    price_unit = fields.Float('Unit Cost', required=True, digits='Product Price')
    sale_price = fields.Float('Sales Price', required=True, digits='Product Price')
    tax_ids = fields.Many2many('account.tax', string='Taxes', help="Taxes that apply on the base amount",
                               compute='_get_computed_taxes', store=True)
    subtotal = fields.Float(string="Subtotal without taxes", compute='compute_subtotal_total', digits='Product Price')
    total = fields.Float(string="Subtotal", compute='compute_subtotal_total', digits='Product Price')
    currency_id = fields.Many2one(comodel_name="res.currency", string="Currency",
                                  default=lambda self: self.env.user.company_id.currency_id)
    sale_line_ids = fields.Many2many(comodel_name="sale.order.line", string="Sale Lines")
    pos_line_ids = fields.Many2many(comodel_name="pos.order.line", string="POS Order Lines")
    branch_id = fields.Many2one(comodel_name="res.branch", string="Branch", required=False, )

    @api.onchange('product_qty', 'price_unit')
    def compute_subtotal(self):
        for line in self:
            line.subtotal = line.product_qty * line.price_unit

    @api.onchange('product_id')
    @api.depends('product_id')
    def _get_computed_taxes(self):
        for line in self:
            tax_ids = self.env['account.tax']
            if line.product_id:
                if line.product_id.supplier_taxes_id:
                    tax_ids = line.product_id.supplier_taxes_id.filtered(
                        lambda tax: tax.company_id == self.env.user.company_id)
            line.tax_ids = tax_ids.ids

    def compute_subtotal_total(self):
        move_line = self.env['account.move.line']
        for line in self:
            res = move_line._get_price_total_and_subtotal_model(line.price_unit, line.product_qty, 0, line.currency_id,
                                                                line.product_id, line.wizard_id.partner_id,
                                                                line.tax_ids, 'in_invoice')
            line.subtotal = res.get('price_subtotal')
            line.total = res.get('price_total')
