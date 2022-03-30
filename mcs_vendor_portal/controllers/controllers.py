# -*- coding: utf-8 -*-
# BRATA BAYU S, S.kom -
from odoo import http
import odoo.http as http
# -*- coding: utf-8 -*-
import werkzeug
import json
import base64
from random import randint
import os
# from docx import

import logging

from odoo import http
from odoo.addons.website.controllers.main import Website
from odoo.http import request
from odoo.addons.web.controllers.main import serialize_exception,content_disposition

from pprint import pprint
from odoo.api import Environment as env

from odoo.http import Response
# import urllib2

class McsGlobalPolicies(http.Controller):
    @http.route('/product', auth='public', website=True)
    def vendorproduk(self, **kw):
    	vendor_id 	= http.request.env.context.get('uid')
    	print("========================================= ID USER LOGIN ",vendor_id)
    	User     	= http.request.env['res.users'].sudo().search([('id', '=', vendor_id)])
    	Partner     = http.request.env['res.partner'].sudo().search([('id', '=', User.partner_id.id)])
    	print("========================================= ID Partner LOGIN ",Partner.id)
    	print("========================================= Name Partner LOGIN ",Partner.name)
    	DTVendor 	= http.request.env['res.partner']
    	return http.request.render('mcs_vendor_portal.product_list', {
            'DTaObject': DTVendor.sudo().search([('id','=',Partner.id)]),
        })


    @http.route('/account', type='http', auth='user', website=True)
    def akunsaya(self, **kw):
    	vendor_id 	= http.request.env.context.get('uid')
    	User     	= http.request.env['res.users'].sudo().search([('id', '=', vendor_id)])
    	Partner     = http.request.env['res.partner'].sudo().search([('id', '=', User.partner_id.id)])
    	DTVendor 	= http.request.env['res.partner']
    	return http.request.render('mcs_vendor_portal.ven_dok', {
            'PartnerData': DTVendor.sudo().search([('id','=',Partner.id)]),
        })


    @http.route('/companygallery/data/<id>', auth='public', website=True)
    def companygallery_data(self, id, **kw):
        DETAILJurnal    = http.request.env['mcs.company_foto_video']
        base_url        = http.request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        attachment      = http.request.env['ir.attachment'].sudo().search([('res_model', '=', 'mcs.company_foto_video'),
                                                                      ('res_field', '=', 'file_pdf'),
                                                                      ('res_id', '=', id)])
        request.cr.execute(""" UPDATE ir_attachment SET public = 't' WHERE res_model = 'mcs.company_foto_video' and res_field = 'file_pdf' and res_id = %s""", (id,))
        # data = request.cr.fetchall()
        url = None
        if attachment:
            url = base_url+attachment.local_url
        return http.request.render('mcs_global_policies.detail_company_foto_video', {
            'detjurnal': DETAILJurnal.sudo().search([('id', '=', id)]),
            'url_file': url
        })


    @http.route('/dok', auth='public', website=True)
    def daily(self, **kw):
    	vendor_id 	= http.request.env.context.get('uid')
    	User     	= http.request.env['res.users'].sudo().search([('id', '=', vendor_id)])
    	Partner     = http.request.env['res.partner'].sudo().search([('id', '=', User.partner_id.id)])
    	DTVendor 	= http.request.env['res.partner']
    	return http.request.render('mcs_vendor_portal.ven_dok', {
    		'PartnerData': DTVendor.sudo().search([('id','=',Partner.id)]),
		})

    @http.route('/mydok', auth='public', website=True)
    def mydok(self, **kw):
    	vendor_id 	= http.request.env.context.get('uid')
    	User     	= http.request.env['res.users'].sudo().search([('id', '=', vendor_id)])
    	Partner     = http.request.env['res.partner'].sudo().search([('id', '=', User.partner_id.id)])
    	DTVendor 	= http.request.env['res.partner']
    	return http.request.render('mcs_vendor_portal.test', {
    		'PartnerData': DTVendor.sudo().search([('id','=',Partner.id)]),
        })


    @http.route('/super_heros/all', auth='public', website=True)
    def super_herosall(self, **kw):
        DTKategori = http.request.env['mcs.super_heros']
        return http.request.render('mcs_global_policies.super_heros_all', {
            'DTaObject': DTKategori.sudo().search([]),
        })

    @http.route('/daily-list', auth='public', website=True)
    def dailylist(self, **kw):
        DTKategori = http.request.env['mcs.daily_news']
        return http.request.render('mcs_global_policies.daily_list', {
            'DTaObject': DTKategori.sudo().search([],limit=5,order='id desc'),
        })

    

    @http.route('/daily/data/<id>', auth='public', website=True)
    def viewdaily(self, id, **kw):
        DETAILJurnal = http.request.env['mcs.daily_news']
        base_url = http.request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        attachment = http.request.env['ir.attachment'].sudo().search([('res_model', '=', 'mcs.daily_news'),
                                                                      ('res_field', '=', 'file_upload'),
                                                                      ('res_id', '=', id)])

        # request.cr.execute(""" UPDATE ir_attachment SET public = 't' WHERE res_model = 'mcs.daily_news' and res_field = 'file_upload' and res_id = %s""", (id,))
        # data = request.cr.fetchall()

        url = None
        if attachment:
            url = base_url+attachment.local_url

        return http.request.render('mcs_global_policies.detail_daily_news', {
            'detjurnal': DETAILJurnal.sudo().search([('id', '=', id)]),
            'url_file': url
        })


    @http.route('/globalpolicies/data/<id>', auth='public', website=True)
    def list(self, id, **kw):
        DETAILJurnal    = http.request.env['mcs.global_policies']
        base_url        = http.request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        request.cr.execute(""" UPDATE ir_attachment SET public = 't' WHERE res_model = 'mcs.global_policies' and res_field = 'file_upload' and res_id = %s""", (id,))
        attachment      = http.request.env['ir.attachment'].sudo().search([('res_model', '=', 'mcs.global_policies'),('res_field', '=', 'file_upload'),('res_id', '=', id)])
        data = request.cr.fetchall() 

        url = None
        if attachment:
            url = base_url+attachment.local_url

        return http.request.render('mcs_global_policies.detailglobalpolicies', {
            'detjurnal': DETAILJurnal.sudo().search([('id', '=', id)]),
            'url_file': url
        })

    @http.route('/globalpolicies/kategori/<id>', auth='public', website=True)
    def list_kategori(self, id, **kw):
        DETAILJurnal = http.request.env['mcs.global_policies_kategori']
        return http.request.render('mcs_global_policies.daftar_survey_bidgasbin', {
            'DTaObject': DETAILJurnal.sudo().search([('id', '=', id)]),
        })

    @http.route('/siteapplication', auth='public', website=True)
    def siteapplication(self, **kw):
        DTKategoriap = http.request.env['mcs.site_application_kategori']
        return http.request.render('mcs_global_policies.siteapplication', {
            'DTaObject': DTKategoriap.sudo().search([]),
        })

    @http.route('/apksite', auth='public', website=True)
    def siteapplication(self, **kw):
        DTKategoriap = http.request.env['mcs.site_application_kategori']
        return http.request.render('mcs_global_policies.siteapplication', {
            'DTaObject': DTKategoriap.sudo().search([],order='name asc'),
        })


    @http.route('/fresh', auth='public', website=True)
    def fresh77(self, **kw):
        DTFresh     = http.request.env['mcs.fresh_77']
        base_url    = http.request.env['ir.config_parameter'].sudo().get_param('web.base.url')

        attachment  = http.request.env['ir.attachment'].sudo().search([('res_model', '=', 'mcs.fresh_77'),
                                                                      ('res_field', '=', 'file_upload')])

        # request.cr.execute(""" UPDATE ir_attachment SET public = 't' WHERE res_model = 'mcs.fresh_77' and res_field = 'file_upload' and res_id = %s""", (id,))
        # data = request.cr.fetchall()

        url = None
        if attachment:
            for attachment in attachment:
                url = base_url+attachment.local_url

        return http.request.render('mcs_global_policies.fresh77', {
            'DTaObject': DTFresh.sudo().search([],order='id desc'),
            'url_file': url
        })

    @http.route('/fresh-list', auth='public', website=True)
    def freshlist(self, **kw):
        DTKategori = http.request.env['mcs.fresh_77']
        return http.request.render('mcs_global_policies.daily_list', {
            'DTaObject': DTKategori.sudo().search([],limit=5),
        })
        
    @http.route('/fresh/data/<id>', auth='public', website=True)
    def freshview(self, id, **kw):
        DETAILJurnal = http.request.env['mcs.fresh_77']
        base_url = http.request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        attachment = http.request.env['ir.attachment'].sudo().search([('res_model', '=', 'mcs.fresh_77'),
                                                                      ('res_field', '=', 'file_upload'),
                                                                      ('res_id', '=', id)])
        url = None
        if attachment:
            url = base_url+attachment.local_url

        return http.request.render('mcs_global_policies.detailfresh77', {
            'detjurnal': DETAILJurnal.sudo().search([('id', '=', id)]),
            'url_file': url
        })

    # @http.route('/fresh77view/data/<id>', auth='public', website=True)
    # def list77(self, id, **kw):
    #     DETAILJurnal = http.request.env['mcs.fresh_77']
    #     base_url = http.request.env['ir.config_parameter'].sudo().get_param('web.base.url')
    #     attachment = http.request.env['ir.attachment'].sudo().search([('res_model', '=', 'mcs.fresh_77'),
    #                                                                   ('res_field', '=', 'file_upload'),
    #                                                                   ('res_id', '=', id)])
    #     url = None
    #     if attachment:
    #         url = base_url+attachment.local_url

    #     return http.request.render('mcs_global_policies.detailfresh77', {
    #         'detjurnal': DETAILJurnal.sudo().search([('id', '=', id)]),
    #         'url_file': url
    #     })



    @http.route('/brata', auth='public', website=True)
    def brata(self, **kw):
        return "Hello, Brata Bayu"



class SSP_JSON():
    def data_output(self, columns, data):
#         pprint(data)
        out = []
          
        i = 0             
        while i < len(data):
            row = []
               
            j = 0             
            while j < len(columns):
                column = columns[j]
                #masukan kolom2
#                 pprint(data[i][column['db']])
                row.insert(column['dt'], data[i][column['db']])    
                j = j + 1
                
            #masukan baris2
            out.append(row)
            i = i + 1
         
#         return "total = " + str(len(columns))
#         pprint(out)
#         return data[1]['first_name']
        return out
    
    def limit(self, requesttt, columns):
        limit = ''

        if (requesttt['start'] and requesttt['length'] != -1):
            limit = " LIMIT " + str(int(requesttt['length'])) + " OFFSET " + str(int(requesttt['start'])) 

        return limit
    
    def order(self, requesttt, columns):
        order = ''
#         pprint(requesttt['order'])
        if (requesttt.get('order', False) and len(requesttt.get('order'))):
            orderBy = []
            dtColumns = self.pluck(columns, 'dt')
#             pprint(dtColumns)
            i = 0
#             pprint(len(requesttt.get('order')))
#             exit(0)
            while i < len(requesttt.get('order')):
                # Convert the column index into the column data property
                columnIdx = int(requesttt.get('order')[i]['column'])
                
                requestColumn = requesttt.get('columns')[columnIdx]
#                 pprint(requestColumn['data'])
                
                columnIdx = dtColumns.index(requestColumn['data'])
                        
                column = columns[columnIdx]
#                 pprint(columnIdx)
                
                
                if (requestColumn['orderable'] == True):
#                     pprint(requesttt.get('order')[i]['dir'])
                    if (requesttt.get('order')[i]['dir'] == 'asc'):
                        dire = 'ASC'
                    else:
                        dire = 'DESC'

                    orderBy.append(column['db'] + ' ' + dire)
                
                i = i + 1
                
#             pprint(orderBy)
            j_orderby = ', '.join(orderBy)
            order = 'ORDER BY ' + j_orderby 
#             pprint(order)
#             exit(0)

        return order
    
    
    def filter(self, requesttt, columns, bindings):
        globalSearch = []
        columnSearch = []
        dtColumns = self.pluck(columns, 'dt')

        if (requesttt['search'] and requesttt['search']['value'] != ''):
            stri = requesttt['search']['value']

            i = 0
            while i < len(requesttt['columns']):
                requestColumn = requesttt['columns'][i]
                columnIdx = dtColumns.index(requestColumn['data'])
                        
                column = columns[columnIdx]

                if (requestColumn['searchable'] == True):
#                     binding = self.bind(bindings, '%' + stri + '%', PDO::PARAM_STR)
                    # binding = self.bindi(bindings, '%' + stri + '%', '')
                    binding = "'%" + stri + "%'"
                    globalSearch.append("" + column['db'] + " LIKE " + binding)
                
                i = i + 1

        # Individual column filtering
        if (requesttt['columns']):
            i = 0
            while i < len(requesttt['columns']):
                requestColumn = requesttt['columns'][i]
                columnIdx = dtColumns.index(requestColumn['data'])
                
                column = columns[columnIdx]

                stri = requestColumn['search']['value']

                if (requestColumn['searchable'] == True and stri != ''):
#                     binding = self.bind(bindings, '%' + str + '%', PDO::PARAM_STR)
                    # binding = self.bindi(bindings, '%' + stri + '%', '')
                    binding = "'%" + stri + "%'"
                    columnSearch.append("" + column['db'] + " LIKE " + binding)
                    
                i = i + 1

        # Combine the filters into a single string
        where = ''

        if (len(globalSearch)):
            where = '(' + ' OR '.join(globalSearch) + ')'
        

        if (len(columnSearch)):
            if (where == ''):
                where = ' AND '.join(columnSearch)
            else:
                where = where + ' AND ' + ' AND '.join(columnSearch)
        

        if (where != ''):
            where = 'WHERE ' + where

        return where
    
    
    def simple(self, requesttt, table, primaryKey, columns):
        bindings = []
        
        
        # Build the SQL query string from the request
        limit = self.limit(requesttt, columns)
        order = self.order(requesttt, columns)
        where = self.filter(requesttt, columns, bindings)
        
        cr, uid, context = request.cr, request.uid, request.context

        # Main query to actually get the data
        sql = "SELECT " + ", ".join(self.pluck(columns, 'db')) + " FROM "+ table +" " + where + order + limit
        print ('================== BRT Query Running : ',sql)
        idp = context.get('id',[])
        cr.execute(sql, (idp))
        data = cr.dictfetchall()        

        # print_r(data)exit

        # Data set length after filtering
        sql = "SELECT COUNT("+primaryKey+") FROM  " + table + " " + where
        cr.execute(sql, (idp))
        resFilterLength = cr.fetchall()
        recordsFiltered = resFilterLength[0][0]

        # Total data set length
        sql = "SELECT COUNT(" + primaryKey + ") FROM " + table + " "
        cr.execute(sql, (idp))
        resTotalLength = cr.fetchall()
        recordsTotal = resTotalLength[0][0]

        #
             # Output
        #
        if (requesttt['draw']):
            draw = int(requesttt['draw'])
        else:
            draw = 0
               
        return {
            "draw" : draw,
            "recordsTotal" : int(recordsTotal),
            "recordsFiltered" : int(recordsFiltered),
            "data" : self.data_output(columns, data),
        }
    
    def complex(self, requesttt, table, primaryKey, columns, whereResult = None, whereAll = None):
        bindings = []

        localWhereResult = []
        localWhereAll = []
        whereAllSql = ''

        # Build the SQL query string from the request
        limit = self.limit(requesttt, columns)
        order = self.order(requesttt, columns)
        where = self.filter(requesttt, columns, bindings)

        whereResult = self._flatten(whereResult)
        whereAll = self._flatten(whereAll)

        if (whereResult):
            if (where):
                where = where + ' AND ' + whereResult 
            else:
                where = 'WHERE ' + whereResult
        

        if (whereAll):
            if (where):
                where = where + ' AND ' + whereAll 
            else:
                where = 'WHERE ' + whereAll

            whereAllSql = 'WHERE ' + whereAll
            
        cr, uid, context = request.cr, request.uid, request.context
        idp = context.get('id',[])
        
        # Main query to actually get the data
        sql = "SELECT `" + "`, `".join(self.pluck(columns, 'db')) + "` FROM `" + table + "` " + where + order + limit
        cr.execute(sql, (idp))
        data = cr.fetchall() 
        
        # Data set length after filtering
        sql = "SELECT COUNT(`"+primaryKey+"`) FROM  `" + table + "`" + where
        cr.execute(sql, (idp))
        resFilterLength = cr.fetchall()
        recordsFiltered = resFilterLength[0][0]
        
        # Total data set length
        sql = "SELECT COUNT(`" + primaryKey + "`) FROM `" + table + "`"
        cr.execute(sql, (idp))
        resTotalLength = cr.fetchall()
        recordsTotal = resTotalLength[0][0]

        #/*
             #* Output
        #*/
        if (requesttt['draw']):
            draw = int(requesttt['draw'])
        else:
            draw = 0
               
        return {
            "draw" : draw,
            "recordsTotal" : int(recordsTotal),
            "recordsFiltered" : int(recordsFiltered),
            "data" : self.data_output(columns, data),
        }
        

    def fatal(self, msg):
        print ('========== PRINT Respon Error ====== ',json.dumps({"error" : msg}))

        exit(0)

    
    def bindi(self, a, val, tipe):
        key = ':binding_' + len(a)

        a.append({'key' : key, 'val' : val,'type' : tipe})

        return key
    
    
    def pluck(self, a, prop):
        out = []

        i = 0
        while i < len(a):
            out.append(a[i][prop])
            
            i = i + 1
        
        return out
    
    
    def _flatten(self, a, joini = ' AND '):
        if (a is not None):
            return ''
        elif (a and isinstance(a, list)):
            return join(joini, a)
        
        return a
    