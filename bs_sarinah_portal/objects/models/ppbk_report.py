# -*- coding: utf-8 -*-
from datetime import timezone, datetime

from odoo import api, fields, models
from odoo.http import request

class PPBKReport(models.TransientModel):
    _name = 'ppbk.report'
    _description = 'PPBK Report'

    def get_report_data(self, **kwargs):
        partner_id = self.env['res.partner'].browse(int(self.env.context.get('partner_id')))
        branch_id = self.env['res.branch'].browse(int(self.env.context.get('branch_id')))
        start_date = self.env.context.get('start_date')
        end_date = self.env.context.get('end_date')
        product_obj = self.env['product.product']
        products = product_obj.search([('owner_id', '=', partner_id.id)])
        brands = partner_id.brand_ids
        pos_order_obj = self.env['pos.order']
        pos_orders = pos_order_obj.search([('date_order', '>=', start_date), ('date_order', '<=', end_date),
                                           ('config_id.branch_id', '=', branch_id.id)])
        order_lines = pos_orders.mapped('lines').filtered(lambda l: l.product_owner_id == partner_id)
        orders = []
        profit_sharings = []
        orders_products = order_lines.mapped('product_id')
        orders_qty = orders_subtotal = orders_discount = orders_total = orders_ppn = orders_omset = 0
        profit_smargin = profit_vmargin = profit_sdiscount = profit_vdiscount = profit_sincome = profit_vincome = 0
        for product in orders_products:
            product_lines = order_lines.filtered(lambda l: l.product_id == product)
            subtotal = 0
            discount = 0
            for line in product_lines:
                subtotal += line.price_unit*line.qty
            for line in product_lines:
                discount += line.price_unit*line.qty*line.discount/100 + line.fix_discount
            sales_qty = sum(product_lines.mapped('qty'))
            tax_amount = abs(sum(product_lines.mapped('price_subtotal'))-sum(product_lines.mapped('price_subtotal_incl')))
            omset_amount = sum(product_lines.mapped('price_subtotal'))
            orders.append({
                'product_id': product,
                'qty': sales_qty,
                'subtotal': subtotal,
                'discount': discount,
                'total': subtotal-discount,
                'taxes_amount': tax_amount,
                'omset_amount': omset_amount
            })
            orders_qty += sales_qty
            orders_subtotal += subtotal
            orders_discount += discount
            orders_total += (subtotal-discount)
            orders_ppn += tax_amount
            orders_omset += omset_amount

            cons_margins = list(set(product_lines.mapped('consignment_margin')))
            for margin in cons_margins:
                margin_lines = product_lines.filtered(lambda l: l.consignment_margin == margin)
                vendor_shares = list(set(margin_lines.mapped('vendor_shared')))
                for share in vendor_shares:
                    shared_lines = product_lines.filtered(lambda l: l.vendor_shared == share)
                    subtotal = 0
                    for line in shared_lines:
                        subtotal += line.price_unit * line.qty
                    vendor_margin = 100-margin
                    sarinah_margin = margin
                    vendor_margin_amount = vendor_margin / 110 * subtotal
                    sarinah_margin_amount = sarinah_margin / 110 * subtotal
                    discount = 0
                    for line in shared_lines:
                        discount += line.price_unit * line.qty * line.discount / 100 + line.fix_discount
                    vendor_shared = share
                    sarinah_shared = 100-share
                    if discount == 0 and vendor_shared == 0:
                        sarinah_shared = 0
                    vendor_shared_amount = vendor_shared/110*discount
                    sarinah_shared_amount = sarinah_shared/110*discount
                    profit_sharings.append({
                        'product_id': product,
                        'sarinah_margin': sarinah_margin,
                        'sarinah_margin_amount': sarinah_margin_amount,
                        'vendor_margin': vendor_margin,
                        'vendor_margin_amount': vendor_margin_amount,
                        'sarinah_shared': sarinah_shared,
                        'sarinah_shared_amount': sarinah_shared_amount,
                        'vendor_shared': vendor_shared,
                        'vendor_shared_amount': vendor_shared_amount,
                        'sarinah_income': sarinah_margin_amount-sarinah_shared_amount,
                        'vendor_income': vendor_margin_amount-vendor_shared_amount,
                    })
                    profit_smargin += sarinah_margin_amount
                    profit_vmargin += vendor_margin_amount
                    profit_sdiscount += sarinah_shared_amount
                    profit_vdiscount += vendor_shared_amount
                    profit_sincome += (sarinah_margin_amount-sarinah_shared_amount)
                    profit_vincome += (vendor_margin_amount-vendor_shared_amount)

        discount_obj = self.env['pos.custom.discount']
        discounts = discount_obj.search([('vendor_id', '=', partner_id.id), ('available_in_pos.branch_id', 'in', branch_id.ids)])
        bills = self.env['account.move'].search([
            ('partner_id', '=', partner_id.id),
            ('is_consignment', '=', True),
            ('invoice_date', '>=', start_date),
            ('invoice_date', '<=', end_date),
            ('state', '!=', 'cancel'),
        ])
        if start_date:
            start_date = fields.Datetime.context_timestamp(self, datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S')).strftime('%d/%m/%Y %H:%M')
            end_date = fields.Datetime.context_timestamp(self, datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S')).strftime('%d/%m/%Y %H:%M')
        return {
            'report_type': 'html',
            'currency': self.env.user.company_id.currency_id,
            'company': self.env.user.company_id,
            'start_date': start_date or '',
            'end_date': end_date or '',
            'brands': brands,
            'products': products,
            'orders': orders,
            'orders_summary': [orders_qty, orders_subtotal, orders_discount, orders_total, orders_ppn, orders_omset],
            'profit_summary': [profit_smargin, profit_vmargin, profit_sdiscount, profit_vdiscount, profit_sincome, profit_vincome],
            'profit_sharings': profit_sharings,
            'partner': partner_id,
            'branch': branch_id,
            'order_lines': order_lines,
            'discounts': discounts,
            'bills': bills
        }

    def _get_html(self):
        result = {}
        rcontext = self.get_report_data()
        report_template = self.env.ref('bs_sarinah_portal.web_ppbk_report')
        result['html'] = report_template.render(rcontext)
        return result

    @api.model
    def get_html(self, given_context=None):
        res = self.search([('create_uid', '=', self.env.uid)], limit=1)
        if not res:
            return self.create({}).with_context(given_context)._get_html()
        return res.with_context(given_context)._get_html()
