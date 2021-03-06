# -*- coding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Devintelle Solutions (<http://devintellecs.com/>).
#
##############################################################################

from odoo import models, fields, api, _
from io import StringIO, BytesIO
from operator import itemgetter
from xlwt import easyxf
import itertools
import datetime
import operator
import calendar
import base64
import xlwt


class dev_stock_inventory(models.TransientModel):
    _name = "dev.stock.inventory"

    @api.model
    def _get_company_id(self):
        return self.env.user.company_id
    
    def _get_daterange(self, date=datetime.datetime.now(), daterange='monthly'):
        year = fields.Date.from_string(date).strftime('%Y')
        month = fields.Date.from_string(date).strftime('%m')
        day = fields.Date.from_string(date).strftime('%d')
        if daterange == 'daily':
            date_from = '{}-{}-{}'.format(year, month, day)
            date_to = '{}-{}-{}'.format(year, month, day)
        elif daterange == 'monthly':
            date_from = '{}-{}-01'.format(year, month)
            date_to = '{}-{}-{}'.format(year, month, str(calendar.monthrange(int(year), int(month))[1]).zfill(2))
        else:
            date_from = '{}-01-01'.format(year)
            date_to = '{}-12-31'.format(year)
        return date_from, date_to
    
    def get_location(self, wh=False):
        return self.env['stock.location'].search([
            ('parent_path', '=like', wh.view_location_id.parent_path + '%') if wh else ('id', '!=', False),
            ('id', 'in', self.location_ids.ids) if self.location_ids else ('id', '!=', False)
        ])
    
    def get_scrap_location(self, wh=False):
        return self.env['stock.location'].search([
            ('parent_path', '=like', wh.view_location_id.parent_path + '%') if wh else ('id', '!=', False),
            ('id', 'in', self.location_ids.ids) if self.location_ids else ('id', '!=', False),
            ('scrap_location', '=', True)
        ])
    
    def get_return_location(self, wh=False):
        return self.env['stock.location'].search([
            ('parent_path', '=like', wh.view_location_id.parent_path + '%') if wh else ('id', '!=', False),
            ('id', 'in', self.location_ids.ids) if self.location_ids else ('id', '!=', False),
            ('return_location', '=', True)
        ])

    name = fields.Char('Name', default=lambda self:'Inventory Stock', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=_get_company_id)
    warehouse_ids = fields.Many2many('stock.warehouse', string='Warehouse', required=True)
    location_ids = fields.Many2many('stock.location', string='Location', domain="[('usage','=','internal')]")
    start_date = fields.Date('Start Date', required=True, default=lambda self:self._get_daterange()[0])
    end_date = fields.Date('End Date', required=True, default=lambda self:self._get_daterange()[1])
    filter_by = fields.Selection([('product', 'Product'), ('category', 'Product Category')], string='Filter By', default=lambda self:False)
    category_id = fields.Many2one('product.category', string='Category')
    product_ids = fields.Many2many('product.product', string='Products')
    is_group_by_category = fields.Boolean('Group By Category')
    is_zero = fields.Boolean('With Zero Values')
    is_value = fields.Boolean('Valuation', default=lambda self:True)

#     
#     def get_before_incoming_qty(self,product, warehouse_id):
#         state = 'done'
#         move_type = 'incoming'
#         m_type = ''
#         if self.location_id:
#             m_type = 'and sm.location_dest_id = %s'
#         query = """select sum(sm.product_uom_qty) from stock_move as sm \
#                               JOIN stock_picking_type as spt ON spt.id = sm.picking_type_id \
#                               JOIN product_product as pp ON pp.id = sm.product_id \
#                               where sm.date < %s and spt.warehouse_id = %s \
#                               and spt.code = %s """ + m_type + """and sm.product_id = %s \
#                               and sm.state = %s and sm.company_id = %s
#                               """
# 
#         start_date = str(self.start_date) + ' 00:00:00'
#         if self.location_id:
#             params = (start_date,warehouse_id.id, move_type, self.location_id.id, self.production_id.id, product.id, state,
#                       self.company_id.id)
#         else:
#             params = (start_date, warehouse_id.id, move_type, product.id, state, self.company_id.id)
# 
#         self.env.cr.execute(query, params)
#         result = self.env.cr.dictfetchall()
#         if result[0].get('sum'):
#             return result[0].get('sum')
#         return 0.0
# 
#     
#     def get_before_outgoing_qty(self, product, warehouse_id):
#         state = 'done'
#         move_type = 'outgoing'
#         m_type = ''
#         if self.location_id:
#             m_type = 'and sm.location_id = %s'
# 
#         query = """select sum(sm.product_uom_qty) from stock_move as sm \
#                                   JOIN stock_picking_type as spt ON spt.id = sm.picking_type_id \
#                                   JOIN product_product as pp ON pp.id = sm.product_id \
#                                   where sm.date < %s and spt.warehouse_id = %s \
#                                   and spt.code = %s """ + m_type + """and sm.product_id = %s \
#                                   and sm.state = %s and sm.company_id = %s
#                                   """
# 
#         start_date = str(self.start_date) + ' 00:00:00'
# 
#         if self.location_id:
#             params = (start_date, warehouse_id.id, move_type, self.location_id.id, self.production_id.id,product.id, state,
#                       self.company_id.id)
#         else:
#             params = (start_date, warehouse_id.id, move_type, product.id, state, self.company_id.id)
# 
#         self.env.cr.execute(query, params)
#         result = self.env.cr.dictfetchall()
#         if result[0].get('sum'):
#             return result[0].get('sum')
#         return 0.0
# 
#     
#     def get_availabel_quantity(self, product, warehouse_id):
#         in_qty = self.get_before_incoming_qty(product, warehouse_id)
#         out_qty = self.get_before_outgoing_qty(product, warehouse_id)
#         adjust_qty = self.get_begining_adjustment_qty(product, warehouse_id)
#         total_qty = in_qty - out_qty + adjust_qty
#         return total_qty
# 
# 
# 
#     
#     def get_begining_adjustment_qty(self, product, warehouse_id):
#         state = 'done'
#         if self.location_id:
#             parent_path = self.location_id.parent_path
#         else:
#             parent_path = warehouse_id.view_location_id.parent_path
# 
#         sq_location_ids = self.env['stock.location'].search([('parent_path', '=like', parent_path + '%')]).ids
# 
#         query = """select sum(sm.product_uom_qty) from stock_move as sm \
#                                   JOIN product_product as pp ON pp.id = sm.product_id \
#                                   where sm.date < %s and \
#                                   sm.location_dest_id in %s and sm.product_id = %s and sm.picking_type_id is null\
#                                   and sm.state = %s and sm.company_id = %s
#                                   """
# 
#         start_date = str(self.start_date) + ' 00:00:00'
# 
#         params = (start_date, tuple(sq_location_ids), product.id, state, self.company_id.id)
# 
#         self.env.cr.execute(query, params)
#         result = self.env.cr.dictfetchall()
#         if result[0].get('sum'):
#             return result[0].get('sum')
#         return 0.0
#         
#     
#     
#     
#     def get_receive_qty(self, product, warehouse_id):
#         state = 'done'
#         move_type = 'incoming'
#         m_type = ''
#         if self.location_id:
#             m_type = 'and sm.location_dest_id = %s'
#         query = """select sum(sm.product_uom_qty) from stock_move as sm \
#                       JOIN stock_picking_type as spt ON spt.id = sm.picking_type_id \
#                       JOIN product_product as pp ON pp.id = sm.product_id \
#                       where sm.date >= %s and sm.date <= %s and spt.warehouse_id = %s \
#                       and spt.code = %s """ + m_type + """and sm.product_id = %s \
#                       and sm.state = %s and sm.company_id = %s
#                       """
# 
#         start_date = str(self.start_date)+ ' 00:00:00'
#         end_date = str(self.end_date) + ' 23:59:59'
# 
#         if self.location_id:
#             params = (start_date, end_date, warehouse_id.id, move_type, self.location_id.id,self.production_id.id, product.id, state,
#                       self.company_id.id)
#         else:
#             params = (start_date, end_date, warehouse_id.id, move_type, product.id, state,self.company_id.id)
# 
#         self.env.cr.execute(query, params)
#         result = self.env.cr.dictfetchall()
#         if result[0].get('sum'):
#             return result[0].get('sum')
#         return 0.0
# 
#     
#     def get_sale_qty(self, product, warehouse_id):
#         state = 'done'
#         move_type = 'outgoing'
#         m_type = ''
#         if self.location_id:
#             m_type = 'and sm.location_id = %s'
# 
#         query = """select sum(sm.product_uom_qty) from stock_move as sm \
#                           JOIN stock_picking_type as spt ON spt.id = sm.picking_type_id \
#                           JOIN product_product as pp ON pp.id = sm.product_id \
#                           where sm.date >= %s and sm.date <= %s and spt.warehouse_id = %s \
#                           and spt.code = %s """ + m_type + """and sm.product_id = %s \
#                           and sm.state = %s and sm.company_id = %s
#                           """
# 
#         start_date = str(self.start_date) + ' 00:00:00'
#         end_date = str(self.end_date) + ' 23:59:59'
# 
#         if self.location_id:
#             params = (start_date, end_date, warehouse_id.id, move_type, self.location_id.id,self.production_id.id, product.id, state,
#                       self.company_id.id)
#         else:
#             params = (start_date, end_date, warehouse_id.id, move_type, product.id, state, self.company_id.id)
# 
#         self.env.cr.execute(query, params)
#         result = self.env.cr.dictfetchall()
#         if result[0].get('sum'):
#             return result[0].get('sum')
#         return 0.0
# 
#     
#     def get_internal_qty(self, product, warehouse_id):
#         state = 'done'
#         move_type = 'internal'
#         m_type = ''
#         if self.location_id:
#             m_type = 'and sm.location_dest_id = %s'
# 
#         query = """select sum(sm.product_uom_qty) from stock_move as sm \
#                               JOIN stock_picking_type as spt ON spt.id = sm.picking_type_id \
#                               JOIN product_product as pp ON pp.id = sm.product_id \
#                               where sm.date >= %s and sm.date <= %s and spt.warehouse_id = %s \
#                               and spt.code = %s """ + m_type + """and sm.product_id = %s \
#                               and sm.state = %s and sm.company_id = %s
#                               """
# 
#         start_date = str(self.start_date) + ' 00:00:00'
#         end_date = str(self.end_date) + ' 23:59:59'
# 
#         if self.location_id:
#             params = (start_date, end_date, warehouse_id.id, move_type, self.location_id.id,self.production_id.id, product.id, state,
#                       self.company_id.id)
#         else:
#             params = (start_date, end_date, warehouse_id.id, move_type, product.id, state, self.company_id.id)
# 
#         self.env.cr.execute(query, params)
#         result = self.env.cr.dictfetchall()
#         if result[0].get('sum'):
#             return result[0].get('sum')
#         return 0.0
# 
#     
#     def get_mrp_qty(self, product, warehouse_id):
#         state = 'done'
#         move_type = 'mrp_operation'
#         m_type = ''
#         if self.location_id:
#             m_type = 'and sm.location_dest_id = %s'
# 
#         query = """select sum(sm.product_qty) from stock_move as sm \
#                               JOIN stock_picking_type as spt ON spt.id = sm.picking_type_id \
#                               JOIN product_product as pp ON pp.id = sm.product_id \
#                               JOIN mrp_production as mp ON mp.id = sm.production_id \
#                               where sm.date >= %s and sm.date <= %s and spt.warehouse_id = %s \
#                               and spt.code = %s """ + m_type + """and sm.product_id = %s \
#                               and sm.state = %s and sm.company_id = %s
#                               """
# 
#         start_date = str(self.start_date) + ' 00:00:00'
#         end_date = str(self.end_date) + ' 23:59:59'
# 
#         if self.location_id:
#             params = (start_date, end_date, warehouse_id.id, move_type, self.location_id.id,self.production_id.id, product.id, state,
#                       self.company_id.id)
#         else:
#             params = (start_date, end_date, warehouse_id.id, move_type, product.id, state, self.company_id.id)
# 
#         self.env.cr.execute(query, params)
#         result = self.env.cr.dictfetchall()
#         if result[0].get('sum'):
#             return result[0].get('sum')
#         return 0.0    
# 
#     
#     def get_pos_adjustment_qty(self, product, warehouse_id,data):
#         state = 'done'
#         if self.location_id:
#             parent_path = self.location_id.parent_path
#         else:
#             parent_path = warehouse_id.view_location_id.parent_path
# 
#         sq_location_ids = self.env['stock.location'].search([('parent_path', '=like', parent_path + '%')]).ids
# 
#         query = """select sum(sm.product_uom_qty) from stock_move as sm \
#                                   JOIN product_product as pp ON pp.id = sm.product_id \
#                                   where sm.date >= %s and sm.date <= %s and \
#                                   sm.location_id in %s and sm.product_id = %s and sm.picking_type_id is null\
#                                   and sm.state = %s and sm.company_id = %s
#                                   """
# 
#         start_date = str(data.start_date) + ' 00:00:00'
#         end_date = str(data.end_date) + ' 23:59:59'
# 
#         params = (start_date, end_date, tuple(sq_location_ids), product.id, state, data.company_id.id)
# 
#         self.env.cr.execute(query, params)
#         result = self.env.cr.dictfetchall()
#         if result[0].get('sum'):
#             return result[0].get('sum')
#         return 0.0
#     
#     
#     def get_neg_adjustment_qty(self, product, warehouse_id,data):
#         state = 'done'
#         if self.location_id:
#             parent_path = self.location_id.parent_path
#         else:
#             parent_path = warehouse_id.view_location_id.parent_path
# 
#         sq_location_ids = self.env['stock.location'].search([('parent_path', '=like', parent_path + '%')]).ids
# 
#         query = """select sum(sm.product_uom_qty) from stock_move as sm \
#                                   JOIN product_product as pp ON pp.id = sm.product_id \
#                                   where sm.date >= %s and sm.date <= %s and \
#                                   sm.location_dest_id in %s and sm.product_id = %s and sm.picking_type_id is null\
#                                   and sm.state = %s and sm.company_id = %s
#                                   """
# 
#         start_date = str(data.start_date) + ' 00:00:00'
#         end_date = str(data.end_date) + ' 23:59:59'
# 
#         params = (start_date, end_date, tuple(sq_location_ids), product.id, state, data.company_id.id)
# 
#         self.env.cr.execute(query, params)
#         result = self.env.cr.dictfetchall()
#         if result[0].get('sum'):
#             return result[0].get('sum')
#         return 0.0
# 
# 
#     def get_product(self):
#         product_pool=self.env['product.product']
#         if not self.filter_by:
#             product_ids = product_pool.search([('type','!=','service')])
#             return product_ids
#         elif self.filter_by == 'product' and self.product_ids:
#             return self.product_ids
#         elif self.filter_by == 'category' and self.category_id:
#             product_ids = product_pool.search([('categ_id','child_of',self.category_id.id),('type','!=','service')])
#             return product_ids
# 
#     
#     def group_by_lines(self,lst):
#         n_lst = sorted(lst, key=itemgetter('category'))
#         groups = itertools.groupby(n_lst, key=operator.itemgetter('category'))
#         group_lines = [{'category': k, 'values': [x for x in v]} for k, v in groups]
#         return group_lines
# 
#     
#     def get_lines(self,warehouse_id):
#         lst=[]
#         product_ids = self.get_product()
#         for product in product_ids:
#             beginning_qty = self.get_availabel_quantity(product, warehouse_id)
#             received_qty = self.get_receive_qty(product, warehouse_id)
#             sale_qty = self.get_sale_qty(product,warehouse_id)
#             internal_qty = self.get_internal_qty(product, warehouse_id)
#             mrp_qty = self.get_mrp_qty(product, warehouse_id)
#             adjust_qty_positive = self.get_pos_adjustment_qty(product, warehouse_id)
#             adjust_qty_negative = self.get_neg_adjustment_qty(product, warehouse_id)
#             adjustment_qty = adjust_qty_positive + adjust_qty_negative
#             adjust_qty = abs(adjustment_qty)
#             ending_qty = (beginning_qty + received_qty + adjust_qty) - sale_qty
#             if not self.is_zero:
#                 if beginning_qty != 0 or received_qty != 0 or sale_qty != 0 or mrp_qty != 0 or adjust_qty != 0 or ending_qty != 0:
#                     lst.append({
#                         'category':product.categ_id.name or 'Untitle',
#                         'product':product.name,
#                         'beginning_qty':beginning_qty,
#                         'received_qty':received_qty,
#                         'sale_qty':sale_qty,
#                         'internal_qty':internal_qty,
#                         'mrp_qty':mrp_qty,
#                         'adjust_qty':adjust_qty,
#                         'ending_qty':ending_qty,
#                     })
#             else:
#                 lst.append({
#                     'category': product.categ_id.name or 'Untitle',
#                     'product': product.name,
#                     'beginning_qty': beginning_qty,
#                     'received_qty': received_qty,
#                     'sale_qty': sale_qty,
#                     'internal_qty': internal_qty,
#                     'mrp_qty': mrp_qty,
#                     'adjust_qty': adjust_qty,
#                     'ending_qty': ending_qty,
#                 })
#         return lst
    
    
    def print_pdf(self):
#         data = self.read()
        datas = {
            'form': self.id
        }
        return self.env.ref('dev_stock_inventory_report.print_dev_stock_inventory').report_action(self, data=datas)

#     
#     def export_stock_ledger(self):
#         workbook = xlwt.Workbook()
#         filename = 'Stock Inventory.xls'
#         # Style
#         main_header_style = easyxf('font:height 400;pattern: pattern solid, fore_color gray25;'
#                                    'align: horiz center;font: color black; font:bold True;'
#                                    "borders: top thin,left thin,right thin,bottom thin")
# 
#         header_style = easyxf('font:height 200;pattern: pattern solid, fore_color gray25;'
#                               'align: horiz center;font: color black; font:bold True;'
#                               "borders: top thin,left thin,right thin,bottom thin")
# 
#         group_style = easyxf('font:height 200;pattern: pattern solid, fore_color gray25;'
#                               'align: horiz left;font: color black; font:bold True;'
#                               "borders: top thin,left thin,right thin,bottom thin")
# 
#         text_left = easyxf('font:height 150; align: horiz left;' "borders: top thin,bottom thin")
#         text_right_bold = easyxf('font:height 200; align: horiz right;font:bold True;' "borders: top thin,bottom thin")
#         text_right_bold1 = easyxf('font:height 200; align: horiz right;font:bold True;' "borders: top thin,bottom thin", num_format_str='0.00')
#         text_center = easyxf('font:height 150; align: horiz center;' "borders: top thin,bottom thin")
#         text_right = easyxf('font:height 150; align: horiz right;' "borders: top thin,bottom thin",
#                             num_format_str='0.00')
# 
#         worksheet = []
#         for l in range(0, len(self.warehouse_ids)):
#             worksheet.append(l)
#         work = 0
#         for warehouse_id in self.warehouse_ids:
#             worksheet[work] = workbook.add_sheet(warehouse_id.name)
#             for i in range(0, 9):
#                 worksheet[work].col(i).width = 140 * 30
# 
#             worksheet[work].write_merge(0, 1, 0, 9, 'STOCK INVENTORY', main_header_style)
# 
#             worksheet[work].write(4, 0, 'Company', header_style)
#             worksheet[work].write(4, 1, 'Warehouse', header_style)
#             worksheet[work].write(4, 2, 'Location', header_style)
#             worksheet[work].write(4, 3, 'Start Date', header_style)
#             worksheet[work].write(4, 4, 'End Date', header_style)
#             worksheet[work].write(4, 5, 'Generated By', header_style)
#             worksheet[work].write(4, 6, 'Generated Date', header_style)
# 
#             worksheet[work].write(5, 0, self.company_id.name, text_center)
#             worksheet[work].write(5, 1, warehouse_id.name, text_center)
#             worksheet[work].write(5, 2, self.location_id.name or '', text_center)
#             start_date = datetime.strptime(self.start_date, '%Y-%m-%d')
#             start_date = start_date.strftime("%d-%m-%Y")
#             worksheet[work].write(5, 3, start_date, text_center)
#             end_date = datetime.strptime(self.end_date, '%Y-%m-%d')
#             end_date = end_date.strftime("%d-%m-%Y")
#             worksheet[work].write(5, 4, end_date, text_center)
#             worksheet[work].write(5, 5, self.env.user.name, text_center)
#             g_date = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
#             worksheet[work].write(5, 6, g_date, text_center)
# 
#             tags = ['Beginning', 'Received', 'Sales', 'Internal', 'Manufacturing' , 'Adjustments', 'Ending']
# 
#             r = 8
#             worksheet[work].write_merge(r, r, 0, 3, 'Products', header_style)
#             c = 4
#             for tag in tags:
#                 worksheet[work].write(r, c, tag, header_style)
#                 c += 1
# 
#             lines = self.get_lines(warehouse_id)
#             if not self.is_group_by_category:
#                 r = 9
#                 b_qty = r_qty = s_qty = i_qty = a_qty = e_qty = m_qty = 0
#                 for line in lines:
#                     b_qty += line.get('beginning_qty')
#                     r_qty += line.get('received_qty')
#                     s_qty += line.get('sale_qty')
#                     i_qty += line.get('internal_qty')
#                     m_qty += line.get('mrp_qty')
#                     a_qty += line.get('adjust_qty')
#                     e_qty += line.get('ending_qty')
#                     worksheet[work].write_merge(r, r, 0, 3, line.get('product'), text_left)
#                     c = 4
#                     worksheet[work].write(r, c, line.get('beginning_qty'), text_right)
#                     c += 1
#                     worksheet[work].write(r, c, line.get('received_qty'), text_right)
#                     c += 1
#                     worksheet[work].write(r, c, line.get('sale_qty'), text_right)
#                     c += 1
#                     worksheet[work].write(r, c, line.get('internal_qty'), text_right)
#                     c += 1
#                     worksheet[work].write(r, c, line.get('mrp_qty'), text_right)
#                     c += 1
#                     worksheet[work].write(r, c, line.get('adjust_qty'), text_right)
#                     c += 1
#                     worksheet[work].write(r, c, line.get('ending_qty'), text_right)
#                     r += 1
#                 worksheet[work].write_merge(r, r, 0, 3, 'TOTAL', text_right_bold)
#                 c = 4
#                 worksheet[work].write(r, c, b_qty, text_right_bold1)
#                 c += 1
#                 worksheet[work].write(r, c, r_qty, text_right_bold1)
#                 c += 1
#                 worksheet[work].write(r, c, s_qty, text_right_bold1)
#                 c += 1
#                 worksheet[work].write(r, c, i_qty, text_right_bold1)
#                 c += 1
#                 worksheet[work].write(r, c, m_qty, text_right_bold1)
#                 c += 1
#                 worksheet[work].write(r, c, a_qty, text_right_bold1)
#                 c += 1
#                 worksheet[work].write(r, c, e_qty, text_right_bold1)
#                 r += 1
#             else:
#                 lines = self.group_by_lines(lines)
#                 r = 9
#                 for l_val in lines:
#                     worksheet[work].write_merge(r, r, 0, 9, l_val.get('category'), group_style)
#                     r += 1
#                     b_qty = r_qty = s_qty = i_qty = a_qty = e_qty = 0
#                     for line in l_val.get('values'):
#                         b_qty += line.get('beginning_qty')
#                         r_qty += line.get('received_qty')
#                         s_qty += line.get('sale_qty')
#                         i_qty += line.get('internal_qty')
#                         m_qty += line.get('mrp_qty')
#                         a_qty += line.get('adjust_qty')
#                         e_qty += line.get('ending_qty')
#                         worksheet[work].write_merge(r, r, 0, 3, line.get('product'), text_left)
#                         c = 4
#                         worksheet[work].write(r, c, line.get('beginning_qty'), text_right)
#                         c += 1
#                         worksheet[work].write(r, c, line.get('received_qty'), text_right)
#                         c += 1
#                         worksheet[work].write(r, c, line.get('sale_qty'), text_right)
#                         c += 1
#                         worksheet[work].write(r, c, line.get('internal_qty'), text_right)
#                         c += 1
#                         worksheet[work].write(r, c, line.get('mrp_qty'), text_right)
#                         c += 1
#                         worksheet[work].write(r, c, line.get('adjust_qty'), text_right)
#                         c += 1
#                         worksheet[work].write(r, c, line.get('ending_qty'), text_right)
#                         r += 1
#                     worksheet[work].write_merge(r, r, 0, 3, 'TOTAL', text_right_bold)
#                     c = 4
#                     worksheet[work].write(r, c, b_qty, text_right_bold1)
#                     c += 1
#                     worksheet[work].write(r, c, r_qty , text_right_bold1)
#                     c += 1
#                     worksheet[work].write(r, c, s_qty , text_right_bold1)
#                     c += 1
#                     worksheet[work].write(r, c, i_qty , text_right_bold1)
#                     c += 1
#                     worksheet[work].write(r, c, m_qty , text_right_bold1)
#                     c += 1
#                     worksheet[work].write(r, c, a_qty , text_right_bold1)
#                     c += 1
#                     worksheet[work].write(r, c, e_qty , text_right_bold1)
#                     r += 1
# 
#             work += 1
# 
#         fp = BytesIO()
#         workbook.save(fp)
#         export_id = self.env['dev.stock.inventory.excel'].create(
#             {'excel_file': base64.encodestring(fp.getvalue()), 'file_name': filename})
#         fp.close()
# 
#         return {
#             'view_mode': 'form',
#             'res_id': export_id.id,
#             'res_model': 'dev.stock.inventory.excel',
#             'view_type': 'form',
#             'type': 'ir.actions.act_window',
#             'target': 'new',
#         }
# 
# 
# class dev_stock_inventory_excel(models.TransientModel):
#     _name = "dev.stock.inventory.excel"
# 
#     excel_file = fields.Binary('Excel Report')
#     file_name = fields.Char('Excel File')

