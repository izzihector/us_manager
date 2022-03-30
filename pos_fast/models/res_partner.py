# -*- coding: utf-8 -*-
##############################################################################
#
#    TL Technology
#    Copyright (C) 2019 ­TODAY TL Technology (<https://www.posodoo.com>).
#    Odoo Proprietary License v1.0 along with this program.
#
##############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class res_partner(models.Model):
    _inherit = "res.partner"

    @api.model
    def create(self, vals):
        partner = super(res_partner, self).create(vals)
        self.env['pos.cache.database'].insert_data(self._inherit, partner.id)
        return partner

    def write(self, vals):
        res = super(res_partner, self).write(vals)
        for partner in self:
            if partner and partner.id != None and partner.active:
                self.env['pos.cache.database'].insert_data(self._inherit, partner.id)
            if partner.active == False:
                self.env['pos.cache.database'].remove_record(self._inherit, partner.id)
        return res

    def unlink(self):
        for record in self:
            self.env['pos.cache.database'].remove_record(self._inherit, record.id)
        return super(res_partner, self).unlink()
