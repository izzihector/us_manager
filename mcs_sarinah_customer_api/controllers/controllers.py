# # -*- coding: utf-8 -*-
# from logging import error
# from odoo import http
# from datetime import datetime
# from odoo.http import request
# import json
# from odoo.exceptions import UserError


# FORMAT_RECEIVER = "%d/%m/%Y"
# FORMAT_DATABASE = "%Y-%m-%d"

# def is_date(value):
#     if datetime.strptime(value, FORMAT_RECEIVER).date():
#         return True
#     return False

# def to_date(value):
#     return datetime.strptime(value, FORMAT_RECEIVER).strftime(FORMAT_DATABASE)

# def generate_data_customer(customer):
#     return {
#         "id": customer.id, 
#         "name": customer.name, 
#         "email": customer.email, 
#         "phone": customer.phone, 
#         "date_of_birth": customer.date_of_birth, 
#         "loyalty_id": customer.barcode,
#         "active": customer.active,
#         "is_user": True if customer.user_ids else False,
#     }

# def generate_error(field, message):
#     return { field: message }

# def date_handler(obj):
#     return obj.isoformat() if hasattr(obj, 'isoformat') else obj

# class McsSarinahCustomerApi(http.Controller):  
#     @http.route('/api/customer', methods=['GET'], auth='public')
#     def get_customers(self):
#         headers = request.httprequest.headers

#         success = False
#         message = ""
#         data = []

#         if 'Sarinah-Key' in headers:
#             auth_user = request.env['ir.config_parameter'].sudo().get_param('mcs_sarinah_key')
#             if headers['Sarinah-Key'] == auth_user:
#                 if id != False:
#                     customers = request.env['res.partner'].sudo().search([('is_customer', '=', True)])
#                     if len(customers) > 0:
#                         success = True

#                         for customer in customers:
#                             data.append(generate_data_customer(customer))
#                     else:
#                         message  = "Customers' data not available"
#                 else:
#                     message = "ID has not been set"
#             else:
#                 message = "Incorrect Sarinah key"
#         else:
#             message = "Sarinah key has not been set"

#         data = {
#             "success": success,
#             "message": message,
#             "data": data
#         }

#         res = json.dumps(data, default=date_handler)
#         return res

#     @http.route('/api/customer/<int:id>', methods=['GET'], auth='public')
#     def get_single_customer(self, **kw):
#         value = dict(kw)
#         id = value['id']
#         headers = request.httprequest.headers

#         success = False
#         message = ""
#         data = False

#         if 'Sarinah-Key' in headers:
#             auth_user = request.env['ir.config_parameter'].sudo().get_param('mcs_sarinah_key')
#             if headers['Sarinah-Key'] == auth_user:
#                 if id != False:
#                     customer = request.env['res.partner'].sudo().search([('id', '=', id), ('is_customer', '=', True)], limit=1)
#                     if len(customer) > 0:
#                         success = True
#                         data = generate_data_customer(customer)
#                     else:
#                         message  = "Customers' data not available"
#                 else:
#                     message = "ID has not been set"
#             else:
#                 message = "Incorrect Sarinah key"
#         else:
#             message = "Sarinah key has not been set"

#         data = {
#             "success": success,
#             "message": message,
#             "data": data
#         }

#         res = json.dumps(data, default=date_handler)
#         return res

#     @http.route('/api/customer/<int:id>', methods=['PUT'], csrf=False, auth='public')
#     def put_customer(self, **kw):
#         value = dict(kw)
#         id = value['id'] 
#         headers = request.httprequest.headers

#         success = True
#         message = ""
#         data = False
#         error = False
        
#         if 'Sarinah-Key' in headers:
#             auth_user = request.env['ir.config_parameter'].sudo().get_param('mcs_sarinah_key')
#             if headers['Sarinah-Key'] == auth_user:
#                 if id != False:
#                     customer = request.env['res.partner'].sudo().search([('id', '=', id), ('is_customer', '=', True)], limit=1)
#                     if len(customer) > 0:
                        
#                         if 'email' in value and value['email'] != "":
#                             cekEmail = request.env['res.partner'].sudo().search([('email', '=', value['email']), ('id', '!=', customer.id)], limit=1)
#                             if len(cekEmail) > 0:
#                                 success = False
#                                 message = "Please correct the data given"
#                                 error = generate_error("email", "Email already used")
                                
#                         if success == True:
#                             if 'date_of_birth' in value and value['date_of_birth'] != "":
#                                 if is_date(value['date_of_birth']) == False:
#                                     success = False
#                                     message = "Please correct the data given"
#                                     error = generate_error("date_of_birth", "Date of Birth has the incorrect date string format. It should be DD/MM/YYYY")

#                         if success == True:
#                             if 'name' in value and value['name'] != "":
#                                 customer.name = value['name']
#                             if 'phone' in value and value['phone'] != "":
#                                 customer.phone = value['phone']
#                             if 'date_of_birth' in value and value['date_of_birth'] != "":
#                                 customer.date_of_birth = to_date(value['date_of_birth'])
#                             if 'email' in value and value['email'] != "":
#                                 customer.email = value['email']
#                             if 'loyalty_id' in value and value['loyalty_id'] != "":
#                                 customer.barcode = value['loyalty_id']

#                             data = generate_data_customer(customer)
#                     else:
#                         message  = "Customers' data not available"
#                 else:
#                     message = "ID has not been set"
#             else:
#                 message = "Incorrect Sarinah key"
#         else:
#             message = "Sarinah key has not been set"
        
#         if success == True:
#             data = {
#                 "success": success,
#                 "message": message,
#                 "data": data
#             }
#         else:
#             data = {
#                 "success": success,
#                 "message": message,
#                 "error": error
#             }

#         res = json.dumps(data, default=date_handler)
#         return res

#     @http.route('/api/customer/<int:id>', methods=['DELETE'], csrf=False, auth='public')
#     def delete_customer(self, **kw):
#         value = dict(kw)
#         id = value['id'] 
#         headers = request.httprequest.headers

#         success = False
#         message = ""
#         data = False
#         error = False
        
#         if 'Sarinah-Key' in headers:
#             auth_user = request.env['ir.config_parameter'].sudo().get_param('mcs_sarinah_key')
#             if headers['Sarinah-Key'] == auth_user:
#                 if id != False:
#                     customer = request.env['res.partner'].sudo().search([('id', '=', id), ('is_customer', '=', True)], limit=1)
#                     if len(customer) > 0:
#                         if customer.active and customer.user_ids:
#                             # customer.active = 0
#                             success = True
#                             message  = "You cannot archive a contact linked to an internal user"
#                         else:
#                             success = True
#                             message  = "Successfully delete customer data"
#                     else:
#                         message  = "Customers' data not available"
#                 else:
#                     message = "ID has not been set"
#             else:
#                 message = "Incorrect Sarinah key"
#         else:
#             message = "Sarinah key has not been set"
        
#         if success == True:
#             data = {
#                 "success": success,
#                 "message": message,
#                 "data": data
#             }
#         else:
#             data = {
#                 "success": success,
#                 "message": message,
#                 "error": error
#             }

#         res = json.dumps(data, default=date_handler)
#         return res