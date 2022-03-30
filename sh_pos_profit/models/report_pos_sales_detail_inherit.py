# -*- coding: utf-8 -*-
from odoo import models,fields,api,_
import pytz
from datetime import timedelta, datetime
from odoo.exceptions import UserError

class PosDetailWizard(models.TransientModel):
    _inherit='pos.details.wizard'

    filter_product_owner = fields.Boolean(string="Filter Product Owner")
    product_owner_id = fields.Many2one(comodel_name="res.partner", string="Product Owner")
    branch_id = fields.Many2one(comodel_name="res.branch", string="Branch")

    pos_config_ids = fields.Many2many('pos.config', 'pos_detail_configs', domain="[('branch_id', '=', branch_id)]", default=lambda s: s.env['pos.config'].search([]))
    
    @api.onchange('branch_id')
    def _onchange_branch_id(self):
        for rec in self:
            if rec.branch_id:
                domain = [('branch_id', '=', self.branch_id.id)]
                pos_config = self.env['pos.config'].search(domain)
                rec.pos_config_ids = pos_config.ids

    def generate_report(self):
        data = {'date_start': self.start_date, 'date_stop': self.end_date, 'config_ids': self.pos_config_ids.ids, 'product_owner_id': self.product_owner_id.id}
        return self.env.ref('point_of_sale.sale_details_report').report_action([], data=data)

class POSSaelsDetailsReportInherit(models.AbstractModel):
    _inherit='report.point_of_sale.report_saledetails'

    def _get_report_values(self, docids, data=None):
        data = dict(data or {})
        configs = self.env['pos.config'].browse(data['config_ids'])
        data.update(self.get_sale_details(data['date_start'], data['date_stop'], configs.ids, False, data['product_owner_id']))
        return data

    
    @api.model
    def get_sale_details(self, date_start=False, date_stop=False, configs=False, session_ids=False, product_owner_id=False):
        """ Serialise the orders of the day information

        params: date_start, date_stop string representing the datetime of order
        """
        if not configs:
            config_ids = self.env['pos.config'].search([])

        user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
        today = user_tz.localize(fields.Datetime.from_string(fields.Date.context_today(self)))
        today = today.astimezone(pytz.timezone('UTC'))
        if date_start:
            date_start = fields.Datetime.from_string(date_start)
        else:
            # start by default today 00:00:00
            date_start = today

        if date_stop:
            # set time to 23:59:59
            date_stop = fields.Datetime.from_string(date_stop)
        else:
            # stop by default today 23:59:59
            date_stop = today + timedelta(days=1, seconds=-1)

        # avoid a date_stop smaller than date_start
        date_stop = max(date_stop, date_start)

        date_start = fields.Datetime.to_string(date_start)
        date_stop = fields.Datetime.to_string(date_stop)

        if not configs:
            orders = self.env['pos.order'].search([
                # ('lines.product_id.owner_id.id', '=', product_owner_id),
                ('date_order', '>=', date_start),
                ('date_order', '<=', date_stop),
                ('state', 'in', ['paid','invoiced','done']),
                ('config_id', 'in', config_ids.ids)])

            # if product_owner_id:
            #     orders.lines.product_id.filtered(lambda product: product.owner_id.id == product_owner_id)

            pos_session_name = ""
            pos_session_name_arr = []
            for config_id in config_ids:
                if config_id.name:
                    pos_session_name_arr.append(config_id.name)
            if len(pos_session_name_arr) > 0:
                pos_session_name = ", ".join(pos_session_name_arr)
        else:
            orders = self.env['pos.order'].search([
                # ('lines.product_id.owner_id.id', '=', product_owner_id),
                ('date_order', '>=', date_start),
                ('date_order', '<=', date_stop),
                ('state', 'in', ['paid','invoiced','done']),
                ('config_id', 'in', configs)])

            # if product_owner_id:
            #     orders.lines.product_id.filtered(lambda product: product.owner_id.id == product_owner_id)
                
            config_ids = self.env['pos.config'].search([('id', 'in', configs)])
            pos_session_name = ""
            pos_session_name_arr = []
            for config_id in config_ids:
                if config_id.name:
                    pos_session_name_arr.append(config_id.name)
            if len(pos_session_name_arr) > 0:
                pos_session_name = ", ".join(pos_session_name_arr)

        user_currency = self.env.user.company_id.currency_id
        
        print("============================ product_owner_id %s" % product_owner_id)

        total = 0.0
        products_sold = {}
        pos_config = {}
        taxes = {}
        for order in orders:
            currency = order.session_id.currency_id

            for line in order.lines:
                if product_owner_id:
                    print("============================ masuk a")
                    if line.product_id.owner_id.id == product_owner_id:
                        print("============================ masuk b")
                        key = (line.product_id, line.price_unit, line.discount)
                        products_sold.setdefault(key, 0.0)
                        products_sold[key] += line.qty

                        pos_config.setdefault(line.product_id.id, line)

                        if line.tax_ids_after_fiscal_position:
                            line_taxes = line.tax_ids_after_fiscal_position.compute_all(line.price_unit * (1-(line.discount or 0.0)/100.0), currency, line.qty, product=line.product_id, partner=line.order_id.partner_id or False)
                            for tax in line_taxes['taxes']:
                                taxes.setdefault(tax['id'], {'name': tax['name'], 'tax_amount':0.0, 'base_amount':0.0})
                                taxes[tax['id']]['tax_amount'] += tax['amount']
                                taxes[tax['id']]['base_amount'] += tax['base']
                        else:
                            taxes.setdefault(0, {'name': _('No Taxes'), 'tax_amount':0.0, 'base_amount':0.0})
                            taxes[0]['base_amount'] += line.price_subtotal_incl
                            
                        # if user_currency != order.pricelist_id.currency_id:
                        #     total += order.pricelist_id.currency_id._convert(
                        #         order.amount_total, user_currency, order.company_id, order.date_order or fields.Date.today())
                        # else:
                        total += (line.qty * line.price_unit)
                else:
                    print("============================ masuk c")
                    key = (line.product_id, line.price_unit, line.discount)
                    products_sold.setdefault(key, 0.0)
                    products_sold[key] += line.qty

                    pos_config.setdefault(line.product_id.id, line)

                    if line.tax_ids_after_fiscal_position:
                        line_taxes = line.tax_ids_after_fiscal_position.compute_all(line.price_unit * (1-(line.discount or 0.0)/100.0), currency, line.qty, product=line.product_id, partner=line.order_id.partner_id or False)
                        for tax in line_taxes['taxes']:
                            taxes.setdefault(tax['id'], {'name': tax['name'], 'tax_amount':0.0, 'base_amount':0.0})
                            taxes[tax['id']]['tax_amount'] += tax['amount']
                            taxes[tax['id']]['base_amount'] += tax['base']
                    else:
                        taxes.setdefault(0, {'name': _('No Taxes'), 'tax_amount':0.0, 'base_amount':0.0})
                        taxes[0]['base_amount'] += line.price_subtotal_incl
                        
                    # if user_currency != order.pricelist_id.currency_id:
                    #     total += order.pricelist_id.currency_id._convert(
                    #         order.amount_total, user_currency, order.company_id, order.date_order or fields.Date.today())
                    # else:
                    total += (line.qty * line.price_unit)

        st_line_ids = self.env["account.bank.statement.line"].search([('pos_statement_id', 'in', orders.ids)]).ids
        print("=================================== orders.ids %s", orders.ids)
        print("=================================== st_line_ids %s", st_line_ids)

        payment_ids = self.env["pos.payment"].search([('pos_order_id', 'in', orders.ids)]).ids
        if payment_ids:
            self.env.cr.execute("""
                SELECT method.name, sum(amount) total
                FROM pos_payment AS payment,
                     pos_payment_method AS method
                WHERE payment.payment_method_id = method.id
                    AND payment.id IN %s
                GROUP BY method.name
            """, (tuple(payment_ids),))
            payments = self.env.cr.dictfetchall()
        else:
            payments = [] 

        return {
            'pos_session_name': pos_session_name,
            'currency_precision': user_currency.decimal_places,
            'total_paid': user_currency.round(total),
            'payments': payments,
            'company_name': self.env.user.company_id.name,
            'taxes': list(taxes.values()),
            'date_start': fields.Datetime.from_string(date_start) + timedelta(hours=7),
            'date_stop': fields.Datetime.from_string(date_stop) + timedelta(hours=7),
            'products': sorted([{
                'product_id': product.id,
                'sku': product.default_code,
                'price_list': [pricelist.fixed_price for pricelist in self.env["product.pricelist.item"].search([('product_id', '=', product.id)])],
                'product_name': product.name,
                'owner_name': product.owner_id.name,
                'pos_name': pos_config[product.id].order_id.session_id.config_id.name,
                'code': product.default_code,
                'quantity': qty,
                'price_unit': price_unit,
                'discount': discount,
                'cost_price':product.standard_price,
                'uom': product.uom_id.name
            } for (product, price_unit, discount), qty in products_sold.items()], key=lambda l: l['product_name'])
        }