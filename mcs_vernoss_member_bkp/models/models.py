# -*- coding: utf-8 -*-

from odoo import models, fields, api
import requests, json
from odoo.exceptions import UserError

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
            last_name = ''

        payload = {
            "firstName": first_name,  
            "lastName": last_name,  
            "phone": self.phone,  
            "homePhone": self.phone,  
            "email": self.email,  
            "birthday": self.date_of_birth.strftime('%Y-%m-%d')
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
            last_name = ''

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
        res = super(ResPartner, self).create(vals)
        if res.is_loyalty:
            res.create_member_api()
        return res

    def write(self, vals):
        res = super(ResPartner, self).write(vals)
        if self.is_loyalty and 'loyalty_id' not in vals:
            self.update_member_api()
        return res