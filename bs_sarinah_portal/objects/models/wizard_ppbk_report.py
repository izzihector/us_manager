from datetime import timedelta

from odoo import api, fields, models


class WizardPPBKReport(models.TransientModel):
    _name = 'wizard.ppbk.report'
    _description = 'Wizard PPBK Report'

    def _get_default_start_date(self):
        return fields.Datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(hours=7)

    def _get_default_end_date(self):
        return fields.Datetime.now().replace(hour=23, minute=59, second=59, microsecond=0) - timedelta(hours=7)

    partner_id = fields.Many2one(comodel_name="res.partner", string="Vendor", required=False, default=False)
    branch_id = fields.Many2one(comodel_name="res.branch", string="Branch", required=False,
                                default=lambda self: self.env.user.branch_id.id)
    start_date = fields.Datetime(string="Start Date", required=True, default=_get_default_start_date)
    end_date = fields.Datetime(string="End Date", required=True, default=_get_default_end_date)
    line_ids = fields.One2many(comodel_name="wizard.ppbk.report.line", inverse_name="wizard_id", string="Lines")

    def action_confirm(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'bs_sarinah_portal.action_ppbk_report',
            'context': {
                'partner_id': self.partner_id.id,
                'branch_id': self.branch_id.id,
                'start_date': self.start_date,
                'end_date': self.end_date
            },
        }

    @api.onchange('start_date', 'end_date', 'branch_id')
    def onchange_date(self):
        # Preserve current value to update new wizard values.
        current_value = {
            'branch_id': self.branch_id.id,
            'start_date': self.start_date,
            'end_date': self.end_date,
        }
        # Remove all vendors to populate it later.
        self.line_ids.unlink()
        # Rewrite current value due to wizard is reset after doing unlink action to line_ids.
        self.write(current_value)
        # Populate with vendors who available based on current filter.
        if self.start_date and self.end_date and self.branch_id:
            pos_order_obj = self.env['pos.order']
            pos_orders = pos_order_obj.search([('date_order', '>=', self.start_date), ('date_order', '<=', self.end_date),
                                               ('config_id.branch_id', '=', self.branch_id.id)])
            partners = pos_orders.mapped('lines').mapped('product_owner_id')
            for partner in partners:
                self.line_ids.create({
                    'wizard_id': self.id,
                    'partner_id': partner.id
                })


class WizardPPBKReportLine(models.TransientModel):
    _name = 'wizard.ppbk.report.line'

    wizard_id = fields.Many2one(comodel_name="wizard.ppbk.report", string="Wizard", ondelete='cascade')
    partner_id = fields.Many2one(comodel_name="res.partner", string="Vendor", required=True)

    def action_show(self):
        self.wizard_id.partner_id = self.partner_id.id
        return self.wizard_id.action_confirm()
