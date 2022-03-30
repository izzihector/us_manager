# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2016 Devintelle Software Solutions (<http://devintellecs.com>).
#
##############################################################################

from odoo import api, models, fields
import datetime
import calendar


class stock_inv_report(models.AbstractModel):
    _name = 'report.dev_stock_inventory_report.stock_inventory_template'
    _description = 'Stock Inventory Report'
    
    def get_lines(self, data):
        lst = {}
        mrp_module = self.env['ir.module.module'].sudo().search([('name', '=', 'mrp'), ('state', '=', 'installed')])
        sale_module = self.env['ir.module.module'].sudo().search([('name', '=', 'sale'), ('state', '=', 'installed')])
        purchase_module = self.env['ir.module.module'].sudo().search([('name', '=', 'purchase'), ('state', '=', 'installed')])
        product_ids = self.get_product(data)
        scrap_location_ids = data.get_scrap_location().ids
        product_action_id = self.env.ref('stock.stock_product_normal_action').id
        for warehouse_id in data.warehouse_ids:
            lst[warehouse_id.id] = []
            location_ids = data.get_location(warehouse_id).ids
#             return_location_ids = data.get_return_location(warehouse_id).ids
            for product in product_ids:
                sys_end = product.with_context(to_date=str(data.end_date) + ' 23:59:59')
                unit_cost = (sys_end.stock_value / sys_end.qty_at_date) if sys_end.qty_at_date else 0.0
                if data.is_value:
                    avg_val = unit_cost
                else:
                    avg_val = 1.0
                
                beginning_qty = avg_val * (self.get_available_quantity(data, product, location_ids))
                
                received_qty = avg_val * (self.get_received_qty(data, product, location_ids))
                delivered_qty = avg_val * (self.get_delivered_qty(data, product, location_ids))
                
                sale_avg_price = received_sale_qty = delivered_sale_qty = 0.0
                if sale_module:
                    sale_avg_price = self.get_sale_avg_price(data, product)
                    received_sale_qty = avg_val * (self.get_received_qty(data, product, location_ids, transaction='s'))
                    delivered_sale_qty = avg_val * (self.get_delivered_qty(data, product, location_ids, transaction='s'))
                
                received_purchase_qty = delivered_purchase_qty = 0.0
                if purchase_module:
                    received_purchase_qty = avg_val * (self.get_received_qty(data, product, location_ids, transaction='p'))
                    delivered_purchase_qty = avg_val * (self.get_delivered_qty(data, product, location_ids, transaction='p'))
                
                internal_qty_pos = avg_val * (self.get_pos_internal_qty(data, product, location_ids))
                internal_qty_neg = avg_val * (self.get_neg_internal_qty(data, product, location_ids))
                internal_qty = internal_qty_pos - internal_qty_neg
                
                mrp_qty_pos = mrp_qty_neg = 0.0
                if mrp_module:
                    mrp_qty_pos = avg_val * (self.get_pos_mrp_qty(data, product, location_ids))
                    mrp_qty_neg = avg_val * (self.get_neg_mrp_qty(data, product, location_ids))
                mrp_qty = mrp_qty_pos - mrp_qty_neg
                
                adjust_qty_pos = avg_val * (self.get_pos_adjustment_qty(data, product, location_ids))
                adjust_qty_neg = avg_val * (self.get_neg_adjustment_qty(data, product, location_ids))
                adjust_qty = adjust_qty_neg - adjust_qty_pos
                
                scrap_qty_pos = avg_val * (self.get_pos_adjustment_qty(data, product, location_ids, scrap_location_ids))
                scrap_qty_neg = avg_val * (self.get_neg_adjustment_qty(data, product, location_ids, scrap_location_ids))
                scrap_qty = scrap_qty_pos - scrap_qty_neg
                
                ending_qty = (beginning_qty + received_qty + adjust_qty + internal_qty + mrp_qty) - delivered_qty
                
                if not data.is_zero:
                    if beginning_qty != 0 or received_qty != 0 or mrp_qty != 0 or delivered_qty != 0 or  adjust_qty != 0 or ending_qty != 0:
                        lst[warehouse_id.id].append({
                            'category':product.categ_id.name or 'Untitled',
                            'product':product.name_get()[0][1],
                            'product_id':product.id,
                            'product_action_id':product_action_id,
                            'uom':product.uom_id.name,
                            'valuation':avg_val,
                            'beginning_qty':beginning_qty,
                            'received_qty':received_qty - received_sale_qty - received_purchase_qty,
                            'delivered_qty':delivered_qty - delivered_sale_qty - delivered_purchase_qty,
                            'received_sale_qty':received_sale_qty,
                            'delivered_sale_qty':delivered_sale_qty,
                            'received_purchase_qty':received_purchase_qty,
                            'delivered_purchase_qty':delivered_purchase_qty,
                            'internal_qty':internal_qty,
                            'internal_qty_pos': internal_qty_pos,
                            'internal_qty_neg': internal_qty_neg,
                            'mrp_qty':mrp_qty,
                            'mrp_qty_pos':mrp_qty_pos,
                            'mrp_qty_neg':mrp_qty_neg,
                            'adjust_qty':adjust_qty + scrap_qty,
                            'scrap_qty':scrap_qty,
                            'ending_qty':ending_qty,
                            'unit_cost':unit_cost,
                            'avg_price':sale_avg_price
                        })
                else:
                    lst[warehouse_id.id].append({
                        'category':product.categ_id.name or 'Untitled',
                        'product':product.name_get()[0][1],
                        'product_id':product.id,
                        'product_action_id':product_action_id,
                        'uom':product.uom_id.name,
                        'beginning_qty': beginning_qty,
                        'received_qty':received_qty - received_sale_qty - received_purchase_qty,
                        'delivered_qty':delivered_qty - delivered_sale_qty - delivered_purchase_qty,
                        'received_sale_qty':received_sale_qty,
                        'delivered_sale_qty':delivered_sale_qty,
                        'received_purchase_qty':received_purchase_qty,
                        'delivered_purchase_qty':delivered_purchase_qty,
                        'internal_qty': internal_qty,
                        'internal_qty_pos': internal_qty_pos,
                        'internal_qty_neg': internal_qty_neg,
                        'mrp_qty': mrp_qty,
                        'mrp_qty_pos': mrp_qty_pos,
                        'mrp_qty_neg': mrp_qty_neg,
                        'adjust_qty':adjust_qty + scrap_qty,
                        'scrap_qty':scrap_qty,
                        'ending_qty': ending_qty,
                        'unit_cost':unit_cost,
                        'avg_price':sale_avg_price
                    })
        return lst

    
    def get_warehouse_data(self, data):
        return data
        
        
    def get_wizard_data(self, data):
        return data
        
    
    def get_available_quantity(self, data, product, location_ids, location2_ids=False):
        return self.get_pos_begining_qty(data, product, location_ids, location2_ids)\
            -self.get_neg_begining_qty(data, product, location_ids, location2_ids)  # total_qty
    
    
    def get_pos_begining_qty(self, data, product, location_ids, location2_ids=False):
        if product and location_ids and data:
            state = 'done'
    
            query = """
            select
                sum(product_qty)
            from
                stock_move
            where
                date < %s
                and location_dest_id in %s
                and product_id = %s
                and state = %s
                and company_id = %s
            """
    
            start_date = str(data.start_date) + ' 00:00:00'
    
            params = (start_date, tuple(location_ids), product.id, state, data.company_id.id)
    
            self.env.cr.execute(query, params)
            result = self.env.cr.dictfetchall()
            return result[0].get('sum') if result and result[0] and result[0].get('sum') and result[0].get('sum') != None else 0.0
        return 0.0
    
    
    def get_neg_begining_qty(self, data, product, location_ids, location2_ids=False):
        if product and location_ids and data:
            state = 'done'
    
            query = """
            select
                sum(product_qty)
            from
                stock_move
            where
                date < %s
                and location_id in %s
                and product_id = %s
                and state = %s
                and company_id = %s
            """
    
            start_date = str(data.start_date) + ' 00:00:00'
    
            params = (start_date, tuple(location_ids), product.id, state, data.company_id.id)
    
            self.env.cr.execute(query, params)
            result = self.env.cr.dictfetchall()
            return result[0].get('sum') if result and result[0] and result[0].get('sum') and result[0].get('sum') != None else 0.0
        return 0.0
        
    def get_product(self, data):
        product_pool = self.env['product.product']
        if not data.filter_by:
            product_ids = product_pool.search([('type', '!=', 'service')])
            return product_ids
        elif data.filter_by == 'product' and data.product_ids:
            return data.product_ids
        elif data.filter_by == 'category' and data.category_id:
            product_ids = product_pool.search([('categ_id', 'child_of', data.category_id.id), ('type', '!=', 'service')])
            return product_ids
        
    
    def get_pos_adjustment_qty(self, data, product, location_ids, location2_ids=False):
        if product and location_ids and data:
            state = 'done'
    
            query = """
            select
                sum(product_qty)
            from
                stock_move
            where
                date >= %s
                and date <= %s
                and location_id in %s
                """ + ('and location_dest_id in %s' if location2_ids else '') + """
                and product_id = %s
                and picking_type_id is null
                and state = %s
                and company_id = %s
            """
    
            start_date = str(data.start_date) + ' 00:00:00'
            end_date = str(data.end_date) + ' 23:59:59'
    
            if location2_ids:
                params = (start_date, end_date, tuple(location_ids), tuple(location2_ids), product.id, state, data.company_id.id)
            else:
                params = (start_date, end_date, tuple(location_ids), product.id, state, data.company_id.id)
    
            self.env.cr.execute(query, params)
            result = self.env.cr.dictfetchall()
            return result[0].get('sum') if result and result[0] and result[0].get('sum') and result[0].get('sum') != None else 0.0
        return 0.0
    
    
    def get_neg_adjustment_qty(self, data, product, location_ids, location2_ids=False):
        if product and location_ids and data:
            state = 'done'
    
            query = """
            select
                sum(product_qty)
            from
                stock_move
            where
                date >= %s
                and date <= %s
                and location_dest_id in %s
                """ + ('and location_id in %s' if location2_ids else '') + """
                and product_id = %s
                and picking_type_id is null
                and state = %s
                and company_id = %s
            """
    
            start_date = str(data.start_date) + ' 00:00:00'
            end_date = str(data.end_date) + ' 23:59:59'
    
            if location2_ids:
                params = (start_date, end_date, tuple(location_ids), tuple(location2_ids), product.id, state, data.company_id.id)
            else:
                params = (start_date, end_date, tuple(location_ids), product.id, state, data.company_id.id)
    
            self.env.cr.execute(query, params)
            result = self.env.cr.dictfetchall()
            return result[0].get('sum') if result and result[0] and result[0].get('sum') and result[0].get('sum') != None else 0.0
        return 0.0
            
    
    def get_delivered_qty(self, data, product, location_ids, location2_ids=False, transaction=False):
        if product and location_ids and data:
            state = 'done'
            move_type = 'outgoing'
            
            tmap = {
                False:'',
                's':'and not sale_line_id isnull',
                'p':'and not purchase_line_id isnull'
            }
    
            query = """
            with sm as (
                select
                    id,
                    product_qty,
                    picking_type_id
                from
                    stock_move
                where
                    date >= %s
                    and date <= %s
                    and product_id = %s
                    and state = %s
                    and company_id = %s
                    and location_id in %s
                    """ + tmap[transaction] + """
            )
            select
                sum(sm.product_qty)
            from
                sm
            join
                stock_picking_type as spt
            on
                spt.id = sm.picking_type_id
                and spt.code = %s
            """
    
            start_date = str(data.start_date) + ' 00:00:00'
            end_date = str(data.end_date) + ' 23:59:59'
    
            params = (start_date, end_date, product.id, state, data.company_id.id, tuple(location_ids), move_type)
    
            self.env.cr.execute(query, params)
            result = self.env.cr.dictfetchall()
            return result[0].get('sum') if result and result[0] and result[0].get('sum') and result[0].get('sum') != None else 0.0
        return 0.0
        
    
    def get_received_qty(self, data, product, location_ids, location2_ids=False, transaction=False):
        if product and location_ids and data:
            state = 'done'
            move_type = 'incoming'
            
            tmap = {
                False:'',
                's':'and not sale_line_id isnull',
                'p':'and not purchase_line_id isnull'
            }
            
            query = """
            with sm as (
                select
                    id,
                    product_qty,
                    picking_type_id
                from
                    stock_move
                where
                    date >= %s
                    and date <= %s
                    and product_id = %s
                    and state = %s
                    and company_id = %s
                    and location_dest_id in %s
                    """ + tmap[transaction] + """
            )
            select
                sum(sm.product_qty)
            from
                sm
            join
                stock_picking_type as spt
            on
                spt.id = sm.picking_type_id
                and spt.code = %s
            """
    
            start_date = str(data.start_date) + ' 00:00:00'
            end_date = str(data.end_date) + ' 23:59:59'
    
            params = (start_date, end_date, product.id, state, data.company_id.id, tuple(location_ids), move_type)
    
            self.env.cr.execute(query, params)
            result = self.env.cr.dictfetchall()
            return result[0].get('sum') if result and result[0] and result[0].get('sum') and result[0].get('sum') != None else 0.0
        return 0.0
        
    
    def get_pos_internal_qty(self, data, product, location_ids, location2_ids=False):
        if product and location_ids and data:
            state = 'done'
            move_type = 'internal'
    
            query = """
            with sm as (
                select
                    id,
                    product_qty,
                    picking_type_id
                from
                    stock_move
                where
                    date >= %s
                    and date <= %s
                    and product_id = %s
                    and state = %s
                    and company_id = %s
                    and location_dest_id in %s
            )
            select
                sum(sm.product_qty)
            from
                sm
            join
                stock_picking_type as spt
            on
                spt.id = sm.picking_type_id
                and spt.code = %s
            """
    
            start_date = str(data.start_date) + ' 00:00:00'
            end_date = str(data.end_date) + ' 23:59:59'
    
            params = (start_date, end_date, product.id, state, data.company_id.id, tuple(location_ids), move_type)
    
            self.env.cr.execute(query, params)
            result = self.env.cr.dictfetchall()
            return result[0].get('sum') if result and result[0] and result[0].get('sum') and result[0].get('sum') != None else 0.0
        return 0.0
        
    
    def get_neg_internal_qty(self, data, product, location_ids, location2_ids=False):
        if product and location_ids and data:
            state = 'done'
            move_type = 'internal'
    
            query = """
            with sm as (
                select
                    id,
                    product_qty,
                    picking_type_id
                from
                    stock_move
                where
                    date >= %s
                    and date <= %s
                    and product_id = %s
                    and state = %s
                    and company_id = %s
                    and location_id in %s
            )
            select
                sum(sm.product_qty)
            from
                sm
            join
                stock_picking_type as spt
            on
                spt.id = sm.picking_type_id
                and spt.code = %s
            """
    
            start_date = str(data.start_date) + ' 00:00:00'
            end_date = str(data.end_date) + ' 23:59:59'
    
            params = (start_date, end_date, product.id, state, data.company_id.id, tuple(location_ids), move_type)
    
            self.env.cr.execute(query, params)
            result = self.env.cr.dictfetchall()
            return result[0].get('sum') if result and result[0] and result[0].get('sum') and result[0].get('sum') != None else 0.0
        return 0.0

    
    def get_pos_mrp_qty(self, data, product, location_ids, location2_ids=False):
        if product and location_ids and data:
            state = 'done'
            move_type = 'mrp_operation'
    
            query = """
            with sm as (
                select
                    id,
                    product_qty,
                    picking_type_id,
                    production_id
                from
                    stock_move
                where
                    date >= %s
                    and date <= %s
                    and product_id = %s
                    and state = %s
                    and company_id = %s
                    and (location_id in %s or location_dest_id in %s)
            )
            select
                sum(sm.product_qty) from sm
            join stock_picking_type as spt
                on spt.id = sm.picking_type_id
                and spt.code = %s
            join mrp_production as mp on
                mp.id = sm.production_id
            """
    
            start_date = str(data.start_date) + ' 00:00:00'
            end_date = str(data.end_date) + ' 23:59:59'
    
            params = (start_date, end_date, product.id, state, data.company_id.id, tuple(location_ids), tuple(location_ids), move_type)
    
            self.env.cr.execute(query, params)
            result = self.env.cr.dictfetchall()
            return result[0].get('sum') if result and result[0] and result[0].get('sum') and result[0].get('sum') != None else 0.0
        return 0.0
    
    
    def get_neg_mrp_qty(self, data, product, location_ids, location2_ids=False):
        if product and location_ids and data:
            state = 'done'
            move_type = 'mrp_operation'
    
            query = """
            with sm as (
                select
                    id,
                    product_qty,
                    picking_type_id,
                    raw_material_production_id
                from
                    stock_move
                where
                    date >= %s
                    and date <= %s
                    and product_id = %s
                    and state = %s
                    and company_id = %s
                    and (location_id in %s or location_dest_id in %s)
            )
            select
                sum(sm.product_qty) from sm
            join stock_picking_type as spt
                on spt.id = sm.picking_type_id
                and spt.code = %s
            join mrp_production as mp on
                mp.id = sm.raw_material_production_id
            """
    
            start_date = str(data.start_date) + ' 00:00:00'
            end_date = str(data.end_date) + ' 23:59:59'
    
            params = (start_date, end_date, product.id, state, data.company_id.id, tuple(location_ids), tuple(location_ids), move_type)
    
            self.env.cr.execute(query, params)
            result = self.env.cr.dictfetchall()
            return result[0].get('sum') if result and result[0] and result[0].get('sum') and result[0].get('sum') != None else 0.0
        return 0.0
    
    
    def get_sale_avg_price(self, data, product):
        if data and product:
            query = """
            select
                sum(price_subtotal / product_uom_qty)
            from
                sale_order_line
            where
                state in ('sale', 'done')
                and write_date >= %s
                and write_date <= %s
                and product_id = %s
                and company_id = %s
            """
    
            start_date = str(data.start_date) + ' 00:00:00'
            end_date = str(data.end_date) + ' 23:59:59'
    
            params = (start_date, end_date, product.id, data.company_id.id)
    
            self.env.cr.execute(query, params)
            result = self.env.cr.dictfetchall()
            return result[0].get('sum') if result and result[0] and result[0].get('sum') and result[0].get('sum') != None else 0.0
        else:
            return 0.0
        
    
    def get_report_values(self, docids, data=None):
        docs = self.env['dev.stock.inventory'].browse(data['form'])
        return {
            'doc_ids': docs.ids,
            'doc_model': 'dev.stock.inventory',
            'docs': docs,
            'proforma': True,
            'get_warehouse_data':self.get_warehouse_data(docs.warehouse_ids),
            'get_wizard_data':self.get_wizard_data(docs),
            'get_lines':self.get_lines(docs)
        }
        
    
    def _get_report_values(self, docids, data=None):
        return self.get_report_values(docids, data)
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
