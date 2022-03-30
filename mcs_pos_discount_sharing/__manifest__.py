############################################################################
#  Module Name: pos
#  File Name: __manifest__.py
#  Created On: 19/11/2021, 09.39
#  Description: POS Discount Sharing
#  Author: Matrica Consulting - (TPW)
############################################################################
# -*- coding: utf-8 -*-
{
    "name"              : "MCS POS Discount Sharing",
    "summary"           : "POS Discount Sharing",
    "category"          : "POS",
    "application"       : True,
    "version"           : "13.0.1",
    "sequence"          : 1,
    "author"            : "Matrica Consulting - (teguh)",
    "license"           : "Other proprietary",
    "website"           : "http://www.matrica.co.id",
    "description"       : """ http://matrica.co.id/blog/pos/
                              * Fungsi modul ini adalah ...
                          """,
    "depends"           : ['base',
                           'mail',
                           'aspl_pos_discount',
                           'mcs_sarinah_product_api'
                          ],
    # always loaded
    'data'              : [ # --- Security ---
                            #'security/group_access.xml',
                            #'security/ir.model.access.csv',
                            # --- sequence ---
                            # --- Load Data ---
                            'data/sequence.xml',
                            # --- View ---
                            'views/pos_custom_discount_inherit.xml',
                            # --- Wizard ---
                            # --- Reports ---
                            # --- Menu ---
                            #'views/menu.xml',
                          ],
    'demo'              : ['demo/demo.xml',
                          ],
    "qweb"              : ['static/src/xml/marketplace.xml'],
    "images"            : ['static/description/Banner.png'],
    "external_dependencies": {"python": []},
    "installable"       : True,
    "auto_install"      : False,
}

#ctt.
#  buat file model @directory models (modul_namaModel.py)
#  _init_.py ditambahkan nama file model
#  Snipet tp_model_generic atau tp_model_inherit