# -*- coding: utf-8 -*-

from odoo import models, fields, api
import requests, json
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

_BASE_URL = "http://128.199.201.196:8283"
_ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJ2ZXJub3NzIiwic3ViIjoiU0FSSUQiLCJpYXQiOjE2MzM1MzUxMjMsImV4cCI6MTY2NDk4OTIwMCwianRpIjoiMjU2M2JjZDgtZGZiOC00YjM2LWI0MzQtYWE1OTFkMDVlZjZhIn0.kQ96TeZ1JMvZYMbFWUGJM5bxCEo3M-jXSzZyMnnzTNU"
_API_KEY = "bbbc61f4-206b-48c3-a606-2ff634936efb"

class ResPartner(models.Model):
    _inherit = 'res.partner'

    _sql_constraints = [
        ('email_uniq', 'UNIQUE(email)', 'Email must be unique !'),
        ('phone_uniq', 'UNIQUE(phone)', 'Phone must be unique !')
    ]

    loyalty_id = fields.Char("Loyalty ID")
    is_loyalty = fields.Boolean()
    date_of_birth = fields.Date("Date of Birth")

    # hs
    def validate_email(self):
        headers = {
            'content-type': "application/json",
            'Authorization': "Bearer %s" % _ACCESS_TOKEN,
            'Api-Key': _API_KEY,
        }

        url = "%s/loyalty-member/get-member?email=%s" % (_BASE_URL, self.email)

        try:
            res = requests.get(url, headers=headers, verify=False)
            data = json.loads(res.content.decode('utf-8'))
        except:
            return False

        print("===================================== %s" % data)
        raise UserError("die")

    def check_phone_number_api(self, vals):
        headers = {
                'content-type': "application/json",
                'Authorization': "Bearer %s" % _ACCESS_TOKEN,
                'Api-Key': _API_KEY,
            }

        if vals.get('phone'):
            phone = vals.get('phone').replace("+", "").replace("-", "").replace(" ", "")
        else:
            return False

        url = "%s/loyalty-member/get-member?phoneNumber=%s" % (_BASE_URL, phone)

        res = requests.get(url, headers=headers, verify=False)
        data = json.loads(res.content.decode('utf-8'))

        if "responseCode" in data:
            if data["responseCode"] == "00":
                return data["payload"]

        return False
        
    def check_loyalty_id(self, vals):
        headers = {
                'content-type': "application/json",
                'Authorization': "Bearer %s" % _ACCESS_TOKEN,
                'Api-Key': _API_KEY,
            }

        if vals.get('loyalty_id'):
            loyalty_id = vals.get('loyalty_id').replace("+", "").replace("-", "").replace(" ", "")
        else:
            return False

        url = "%s/loyalty-member/get-member?loyaltyMemberId=%s" % (_BASE_URL, loyalty_id)

        res = requests.get(url, headers=headers, verify=False)
        data = json.loads(res.content.decode('utf-8'))

        if "responseCode" in data:
            if data["responseCode"] == "00":
                return data["payload"]

        return False

    def create_member_api(self):
        headers = {
                'content-type' : "application/json",
                'Authorization' : "Bearer %s" % _ACCESS_TOKEN,
                'Api-Key' : _API_KEY,
            }

        url = "%s/loyalty-member/create" % _BASE_URL

        name = self.name
        name_arr = name.split()
        
        first_name = ' '.join(name_arr[0:len(name_arr)-1])
        last_name = name_arr[len(name_arr)-1]

        if not first_name:
            first_name = last_name
            last_name = ' '

        payload = {
            "firstName": first_name,  
            "lastName": last_name,  
            "phone": self.phone,  
            "homePhone": self.phone,  
            "email": self.email,  
            "birthday": self.date_of_birth.strftime('%Y-%m-%d') if self.date_of_birth else "1990-01-01"
        }

        try:
            res = requests.post(url, json=payload, headers=headers, verify=False)
            data = json.loads(res.content.decode('utf-8'))
        except:
            return False

        if data:
            if 'loyaltyMemberId' in data:
                loyaltyMemberId = data['loyaltyMemberId']
                self.loyalty_id = loyaltyMemberId
                self.barcode = "042%s" % loyaltyMemberId
                return True

        return False

    def update_member_api(self):
        headers = {
                'content-type' : "application/json",
                'Authorization' : "Bearer %s" % _ACCESS_TOKEN,
                'Api-Key' : _API_KEY,
            }

        url = "%s/loyalty-member/update-member" % _BASE_URL

        name = self.name
        name_arr = name.split()
        
        first_name = ' '.join(name_arr[0:len(name_arr)-1])
        last_name = name_arr[len(name_arr)-1]

        if not first_name:
            first_name = last_name
            last_name = ' '

        payload = {  
            "loyaltyMemberId": self.loyalty_id, 
            "birthday": self.date_of_birth.strftime('%Y-%m-%d'), 
            "firstName": first_name, 
            "lastName": last_name, 
            "phone": self.phone, 
            "homePhone": self.phone, 
            "email": self.email, 
            "gender": "MALE"
        }

        try:
            res = requests.post(url, json=payload, headers=headers, verify=False)
            json.loads(res.content.decode('utf-8'))
        except:
            return False

        return True

    @api.model
    def create(self, vals):
        if 'is_loyalty' in vals:
            if vals['is_loyalty']:
                check_phone = False
                check_loyalty_id = False
                if 'phone' in vals and vals['phone']:
                    check_phone = True
                elif 'loyalty_id' in vals and vals['loyalty_id']:
                    check_loyalty_id = True
                
                result = False
                if check_loyalty_id or check_phone:
                    if check_loyalty_id:
                        result = self.check_loyalty_id(vals)
                    elif check_phone:
                        result = self.check_phone_number_api(vals)

                if result:
                    vals['name'] = "%s %s" % (result['firstName'], result['lastName'])
                    vals['phone'] = "%s" % (result['phone'])
                    vals['loyalty_id'] = "%s" % (result['loyaltyMemberId'])
                    vals['email'] = "%s" % (result['email'])
                    vals['date_of_birth'] = "%s" % (result['birthday'])
                    res = super(ResPartner, self).create(vals)
                    res.check_wallet_vernoss(res)
                    _logger.warning("=============================================== res %s" % res)
                    return res
                else:
                    res = super(ResPartner, self).create(vals)
                    res.create_member_api()
                    return res
             
        return super(ResPartner, self).create(vals) 

    def write(self, vals):
        res = super(ResPartner, self).write(vals)
        if self.is_loyalty:
            if self.loyalty_id:
                self.update_member_api()
            else:
                vals['phone'] = vals['phone'] or self.phone
                result = self.check_phone_number_api(vals)
                if result:
                    customerLoyalty = self.env['res.partner'].sudo().search([
                            ('loyalty_id', '=', str(result['loyaltyMemberId'])),
                        ])

                    if len(customerLoyalty) < 1:
                        vals['name'] = "%s %s" % (result['firstName'], result['lastName'])
                        vals['phone'] = "%s" % (result['phone'])
                        vals['loyalty_id'] = "%s" % (result['loyaltyMemberId'])
                        vals['email'] = "%s" % (result['email'])
                        vals['date_of_birth'] = "%s" % (result['birthday'])
                        return super(ResPartner, self).write(vals)
                else:
                    self.create_member_api()
        return res