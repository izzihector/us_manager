from logging import currentframe
from math import ceil

from odoo import api, fields, models


class SaleReport(models.Model):
    _inherit = 'sale.report'

    brand_id = fields.Many2one(comodel_name='product.brand', string='Brand', related="product_id.product_tmpl_id.brand_id")
    branch_id = fields.Many2one(related="product_id.product_tmpl_id.branch_id")

    gross_total = fields.Float(string='Gross Total', compute="_compute_gross_total")
    fix_discount = fields.Float(string='Fix Discount', readonly=True)
    pos_discount = fields.Float(string='POS Discount', readonly=True)
    vendor_shared = fields.Float(string='Vendor Shared', readonly=True)
    consignment_margin = fields.Float(string='Consignment Margin', compute="_compute_consignment_margin")

    supplier_gross_revenue = fields.Float(string='Supplier Gross Revenue', compute="_compute_supplier_revenue")
    supplier_discount = fields.Float(string='Supplier Discount', compute="_compute_supplier_revenue")
    supplier_revenue = fields.Float(string='Supplier Revenue', compute="_compute_supplier_revenue")

    supplier_price_subtotal = fields.Float(string='Supplier Price Subtotal', compute="_compute_supplier_price")
    supplier_price_total = fields.Float(string='Supplier Price Total', compute="_compute_supplier_price")

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        res = super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)
        sale_report = res.split('UNION ALL')[0]
        pos_sale_report = res.split('UNION ALL')[1]

        updated_sale_report = ''
        for line in sale_report.split('\n'):
            if 's.pricelist_id as pricelist_id,' == line.strip():
                updated_sale_report += 'NULL as fix_discount,\n'
                updated_sale_report += 'NULL as pos_discount,\n'
                updated_sale_report += 'NULL as vendor_shared,\n'
            updated_sale_report += line + '\n'

        updated_pos_sale_report = ''
        for line in pos_sale_report.split('\n'):
            if 'pos.pricelist_id AS pricelist_id,' == line.strip():
                updated_pos_sale_report += 'l.fix_discount as fix_discount,\n'
                updated_pos_sale_report += 'l.discount as pos_discount,\n'
                updated_pos_sale_report += 'l.vendor_shared as vendor_shared,\n'
            if 'pos.pricelist_id,' == line.strip():
                updated_pos_sale_report += 'l.fix_discount,\n'
                updated_pos_sale_report += 'l.discount,\n'
                updated_pos_sale_report += 'l.vendor_shared,\n'
            updated_pos_sale_report += line + '\n'
        return '%s UNION ALL %s' % (updated_sale_report, updated_pos_sale_report)

    @api.depends('branch_id', 'product_id')
    def _compute_supplier_price(self):
        for record in self:
            product_supplier_id = record.env['product.supplierinfo'].sudo().search([
                ('product_id', '=', record.product_id.id),
                ('branch_id', '=', record.branch_id.id),
            ], limit=1)
            if product_supplier_id:
                record.supplier_price_subtotal = product_supplier_id.price_after_margin
                record.supplier_price_total = product_supplier_id.price_after_margin * record.product_uom_qty
            else:
                record.supplier_price_subtotal = False
                record.supplier_price_total = False

    @api.depends('product_tmpl_id')
    def _compute_consignment_margin(self):
        for record in self:
            vendor_product_id = record.env['vendor.product'].sudo().search([
                ('product_tmpl_id', '=', record.product_tmpl_id.id),
            ], limit=1)
            if vendor_product_id:
                record.consignment_margin = vendor_product_id.margin_percentage
            else:
                record.consignment_margin = False

    @api.depends('fix_discount', 'pos_discount', 'price_total')
    def _compute_gross_total(self):
        for record in self:
            gross_total = record.price_total
            if record.fix_discount:
                gross_total += record.price_total
            if record.pos_discount:
                gross_total += ((gross_total / 100) * record.pos_discount)
            record.gross_total = gross_total

    @api.depends('price_subtotal', 'price_total', 'vendor_shared', 'discount_amount')
    def _compute_supplier_revenue(self):
        for record in self:
            tax = ceil((record.price_total - record.price_subtotal) / record.price_total * 100)
            vendor_margin = (100 - record.consignment_margin)
            # Dicount Beban Mitra
            # -- Disc Beban Mitra = Discount * Vendor Shared % * PPN Include,
            # -- Sample >> 12000 * 80 % * 10 / 11 = 8727
            supplier_discount = record.discount_amount * (record.vendor_shared / 100) * tax / 11
            # Hak Mitra
            # -- Hak Mitra = (Net Sales * Vendor Margin % * PPN Include) + (Discount * Vendor Shared % * PPN Include),
            # -- Sample >> (108000 * 80 % * 10 / 11) + (12000 * 80 % * 10 / 11) = 87273
            supplier_revenue = (record.price_total * (vendor_margin / 100) * tax / 11) + supplier_discount
            # Hak Mitra Setelah Discount
            # -- Hak Mitra Setelah Discount = Hak Mitra - Discount Beban Mitra
            supplier_gross_revenue = supplier_revenue - supplier_discount

            record.supplier_gross_revenue = round(supplier_gross_revenue, 2)
            record.supplier_discount = round(supplier_discount, 2)
            record.supplier_revenue = round(supplier_revenue, 2)
