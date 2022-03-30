# -*- coding: utf-8 -*-
#############################################################################
#
#
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

{
    'name': 'Split Assets In Vendor Bill',
    'category': 'Purchase',
    'summary': "Splitting of assets in vendor bill",
    'depends': ['account','om_account_asset'],
    'author': 'APPSGATE FZC LLC',
    'description': """ 

           asset split,
           split,
          asset management,
       """,
    'data': [

       # 'views/asset_split.xml',

    ],
    'images': [
        'static/src/img/main-screenshot.png'
    ],

    'demo': [
    ],
    'license': 'AGPL-3',
    'price':'8',
    'currency':'USD',
    'application': True,
    'installable': True,
    'auto_install': False,
}
