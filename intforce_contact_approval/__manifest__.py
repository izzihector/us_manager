# -*- coding: utf-8 -*-
# Copyright (C) Intforce Software Private Limited
{
    'name': 'Contacts Approval / Rejection',
    'author': 'Intforce Software Private Limited',
    'website': "https://intforce.co.in",
    "support": "odoo-support@intforce.co.in", 
    'version': '13.0.1',
    'category': 'Human Resources',
    'summary': """
 
""",
    
    'depends': ['base','contacts','sale_management','account','purchase','stock'],
    'data': [
        'security/intforce_mass_approve_contact_security.xml',
        'views/contact_view.xml',
    ],
    'images': ['static/description/background.jpg'],
    "installable": True,
    "auto_install": False,
    "application": True,
    "price": 15,
    "currency": "EUR"    
}
