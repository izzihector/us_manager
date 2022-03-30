# See LICENSE file for full copyright and licensing details.

{
    'name': 'Odoo Whatsapp Integration',
    'summary': 'Odoo Whatsapp Integration provides feature to send the Text Message, Multi-Media files and URL Link to multiple Contacts by using the Chat-API.',
    'description': """
			Odoo Whatsapp Integration
			Odoo Whatsapp Connector
			whatsapp integration in odoo 
			whatsapp integration with odoo 
			odoo whatsapp integration app
			odoo whatsapp integration code
			odoo whatsapp integration github
			odoo whatsapp integration guide
			odoo whatsapp integration key
			odoo whatsapp integration list
			odoo whatsapp integration location
			odoo whatsapp integration online
			odoo whatsapp integration tutorial
			Odoo Whatsapp Integration
			Integration of odoo Whatsapp
			WhatsApp Odoo Integration
			Integrate Odoo with WhatsApp
			whatsapp connector in android
			whatsapp connector download
			whatsapp connector example
			whatsapp connector mobile
			whatsapp connector software
			odoo whatsapp connector android
			odoo whatsapp connector apk
			odoo whatsapp connector app
			odoo whatsapp connector download
			odoo whatsapp connector example
			odoo whatsapp connector ios
			Odoo Account Whatsapp Integration
			Odoo Sale Whatsapp Integration
			Odoo HR Whatsapp Integration
			Odoo HR Payroll Whatsapp Integration
			Odoo Stock Whatsapp Integration
			Odoo POS Whatsapp Integration
			Odoo Whatsapp
			Whatsapp Integration
			Whatsapp Connector
			Whatsapp
    """,
    'version': '13.0.1.0.0',
    'license': 'LGPL-3',
    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'maintainer': 'Serpent Consulting Services Pvt. Ltd.',
    'website': 'http://www.serpentcs.com',
    'sequence': 1,
    'category': 'Extra Tools',
    'depends': [
        'contacts'
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/whatsapp_error_log_cron.xml',
        'views/res_company_view.xml',
        'views/res_partner_view.xml',
        'views/whatsapp_message_log_view.xml',
        'views/mail_template.xml',
        'wizard/whatsapp_message_view.xml',
    ],
    'images': ['static/description/odoo-whatsapp-main.gif'],
    'live_test_url': "https://www.youtube.com/watch?v=KCWIrgVb4xc",
    'installable': True,
    'price': 79,
    'external_dependencies': {'python': ['phonenumbers']},
    'currency': 'EUR'
}
