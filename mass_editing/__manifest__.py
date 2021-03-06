# Copyright 2016 Serpent Consulting Services Pvt. Ltd. (support@serpentcs.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Mass Editing',
    'version': '13.0.1.1.0',
    'author': 'Patch to V13 by Teguh Patria'
              'Matrica Consulting',
    'category': 'Tools',
    'website': 'https://matrica.co.id',
    'license': 'AGPL-3',
    'summary': 'Mass Editing',
    'uninstall_hook': 'uninstall_hook',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/mass_editing_view.xml',
    ],
}
