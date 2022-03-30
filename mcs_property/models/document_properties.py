from odoo import models, fields, api
from odoo.exceptions import UserError


class DocumentProperties(models.Model):
    _name = 'mcs_property.document_properties'
    _description = 'mcs_property.document_properties'

    name = fields.Char(track_visibility=True)
    res_partner_id = fields.Many2one(comodel_name='res.partner', string='Res Partner', ondelete='cascade',
                                     track_visibility=True)
    contract_id = fields.Many2one(comodel_name='mcs_property.contract', string='Contract', ondelete='cascade',
                                     track_visibility=True)
    document_category_id = fields.Many2one(comodel_name='mcs_property.document_categories', string='Document Category',
                                           ondelete='cascade', track_visibility=True)
    file = fields.Binary(string="File", required=True, attachment=True, track_visibility=True)
    file_name = fields.Char(string="File Name", track_visibility=True)

    # @api.model
    # def create(self, values):
    #     document_category = self.env['mcs_property.document_categories'].search(
    #         [('id', '=', values['document_category_id'])], limit=1)
    #     values['name'] = document_category.name
    #     surat = super(DocumentProperties, self).create(values)
    #     return surat

    @api.onchange('res_partner_id')
    def _change_doc_cat(self):
        domain = []
        if self.res_partner_id:
            ids = []
            document_properties = self.env['mcs_property.document_properties'].search(
                [('res_partner_id', '=', self.res_partner_id._origin.id)])
            for doc_prop in document_properties:
                ids.append(doc_prop.document_category_id.id)

            domain = [('id', 'not in', ids)]

        return {'domain': {'document_category_id': domain}}

    @api.onchange('contract_id')
    def _change_doc_cat(self):
        domain = []
        if self.contract_id:
            ids = []
            document_properties = self.env['mcs_property.document_properties'].search(
                [('contract_id', '=', self.contract_id._origin.id)])
            for doc_prop in document_properties:
                ids.append(doc_prop.document_category_id.id)

            domain = [('id', 'not in', ids)]

        return {'domain': {'document_category_id': domain}}

    @api.onchange('document_category_id')
    def _change_name(self):
        for values in self:
            document_category = self.env['mcs_property.document_categories'].search(
                [('id', '=', self.document_category_id.id)], limit=1)
            values.name = document_category.name
