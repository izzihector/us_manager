# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import http, sql_db, api, registry
from odoo.tools import date_utils
from odoo.tools.misc import DEFAULT_SERVER_DATE_FORMAT
from odoo.tools.safe_eval import safe_eval
import json
import multiprocessing as mp
# from contextlib import closing


class BaseRmdoo(http.Controller):
    
#     @http.route('/pivot/json/parallel/<int:part>', auth='user')
#     def pivot_json_parallel(self, part, **kw):
#          
#         models_obj = http.request.env['ir.model']
#         fields_obj = http.request.env['ir.model.fields']
#         model = kw['model']
#         obj = http.request.env[model]
#         record = obj.browse(safe_eval(kw['record']))
#         visible_attributes = kw.get('fields') and safe_eval(kw.get('fields')) or []
#          
#         output = mp.Queue()
#         nice_lines = []
#          
#         def part_process(part_ids):
#             with sql_db.db_connect(obj._cr.dbname).cursor() as cr:
#                 cr.execute('select * from %s where id in %s' % (obj._table, '%s'), (tuple(part_ids),))
#                 print(cr.dictfetchall())
# #             cr = registry(obj._cr.dbname).cursor()
# #             part_obj = obj.with_env(obj.env(cr=cr))
# #             try:
# #                 print(part_obj.browse(part_ids).read())
# #             finally:
# #                 part_obj._cr.close()
#                  
#         item_ids = record.read(['id'])
#         parts_ids = []
#         part_size = part or 10
#         for part_pos in range(0, len(item_ids), part_size):
#             buffer1 = []
#             for buffer2 in item_ids[part_pos:part_pos + part_size]:
#                 buffer1.append(buffer2['id'])
#             parts_ids.append(buffer1)
#          
#         processes = [mp.Process(target=part_process, args=(part_ids,)) for part_ids in parts_ids]
#         for p in processes:
#             p.start()
#         for p in processes:
#             p.join()
#         results = [output.get() for p in processes]
#         print(results)
#          
#         ret = json.dumps(nice_lines, default=date_utils.json_default)
#         return ret

    @http.route('/pivot/json', auth='user')
    def pivot_json(self, **kw):
        
        models_obj = http.request.env['ir.model']
        fields_obj = http.request.env['ir.model.fields']
        model = kw['model']
        obj = http.request.env[model]
        record = obj.browse(safe_eval(kw['record']))
        visible_attributes = kw.get('fields') and safe_eval(kw.get('fields')) or []
        
        nice_lines = []
        list_items = []
        if visible_attributes:
            field_to_read = []
            model_info = models_obj._get(model)
            for field in model_info.field_id:
                for visible_attribute in visible_attributes:
                    if (field.name == visible_attribute) or (field.field_description == visible_attribute):
                        field_to_read.append(field.name)
            list_items = record.read(list(set(field_to_read)))
        else:
            list_items = record.read()
        for items in list_items:
            item_dict = {}
            for (key, value) in items.items():
                field_info = fields_obj._get(model, key)
                if True:  # field_info.ttype not in ['many2many', 'one2many']:
                    nice_key = field_info.field_description
                    if (not visible_attributes) or (nice_key in visible_attributes) or (key in visible_attributes):
                        try:
                            if value and (field_info.ttype in ['many2one']) and (field_info.relation == 'product.product'):
                                prod = http.request.env[field_info.relation].browse(value[0])
                                item_dict['%s (Variant)' % (nice_key)] = prod.name_get()[0][1] or ''
                                item_dict['%s' % (nice_key)] = prod.product_tmpl_id.name_get()[0][1] or ''
                                item_dict['%s (Category)' % (nice_key)] = prod.categ_id.name_get()[0][1] or ''
                            elif value and (field_info.ttype in ['many2many', 'one2many']):
                                objs = http.request.env[field_info.relation].browse(value)
                                name_list = []
                                for obj in objs:
                                    name_list.append(obj.name_get()[0][1])
                                item_dict[nice_key] = '(%s)' % (','.join(name_list))
                            elif value and (field_info.ttype in ['date', 'datetime']):
                                item_dict[nice_key] = value.strftime(DEFAULT_SERVER_DATE_FORMAT) or ''
                                item_dict['%s (Year)' % (nice_key)] = value.strftime("%Y") or ''
                                item_dict['%s (Month)' % (nice_key)] = value.strftime("%m") or ''
                                item_dict['%s (Day)' % (nice_key)] = value.strftime("%d") or ''
                            elif value and (field_info.ttype in ['selection']):
                                item_dict[nice_key] = dict(http.request.env[model]._fields.get(key)._description_selection(http.request.env)).get(value) or ''
                            elif value and (isinstance(value, tuple) and len(value) > 1):
                                item_dict[nice_key] = value[1] or ''
                            else:
                                item_dict[nice_key] = value if value not in [None, False] else ''
                        except:
                            item_dict[nice_key] = value if value not in [None, False] else ''
            nice_lines.append(item_dict)
        ret = json.dumps(nice_lines, default=date_utils.json_default)
        return ret
    
#     @http.route('/base_rmdoo/base_rmdoo/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/base_rmdoo/base_rmdoo/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('base_rmdoo.listing', {
#             'root': '/base_rmdoo/base_rmdoo',
#             'objects': http.request.env['base_rmdoo.base_rmdoo'].search([]),
#         })

#     @http.route('/base_rmdoo/base_rmdoo/objects/<model("base_rmdoo.base_rmdoo"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('base_rmdoo.object', {
#             'object': obj
#         })
