# -*- coding: utf-8 -*-
import itertools

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    archive_reason = fields.Selection(string="Archive Reason", selection=[
        ('approval', 'Need to Approve'),
        ('manual', 'Manual Operation')], default='approval', copy=False)
    create_department_id = fields.Many2one(comodel_name="hr.department", string="Department", store=True,
                                           related='create_uid.department_id')
    is_coupon = fields.Boolean(string='Coupon')

    @api.model
    def create(self, vals):
        vals['active'] = False
        return super(ProductTemplate, self).create(vals)

    def write(self, vals):
        if vals.get('active') and not self.env.user.has_group('bs_sarinah_product.group_product_approval'):
            raise ValidationError("Sorry you are not allowed to approve/activate product.")
        if 'active' in vals:
            if vals.get('active') is False:
                vals['archive_reason'] = 'manual'
            else:
                vals['archive_reason'] = ''
        return super(ProductTemplate, self).write(vals)

    # override to archive new product.product
    def _create_variant_ids(self):
        self.flush()
        Product = self.env["product.product"]

        variants_to_create = []
        variants_to_activate = Product
        variants_to_unlink = Product

        for tmpl_id in self:
            lines_without_no_variants = tmpl_id.valid_product_template_attribute_line_ids._without_no_variant_attributes()

            all_variants = tmpl_id.with_context(active_test=False).product_variant_ids.sorted(lambda p: (p.active, -p.id))

            current_variants_to_create = []
            current_variants_to_activate = Product

            # adding an attribute with only one value should not recreate product
            # write this attribute on every product to make sure we don't lose them
            single_value_lines = lines_without_no_variants.filtered(lambda ptal: len(ptal.product_template_value_ids._only_active()) == 1)
            if single_value_lines:
                for variant in all_variants:
                    combination = variant.product_template_attribute_value_ids | single_value_lines.product_template_value_ids._only_active()
                    # Do not add single value if the resulting combination would
                    # be invalid anyway.
                    if (
                        len(combination) == len(lines_without_no_variants) and
                        combination.attribute_line_id == lines_without_no_variants
                    ):
                        variant.product_template_attribute_value_ids = combination

            # Set containing existing `product.template.attribute.value` combination
            existing_variants = {
                variant.product_template_attribute_value_ids: variant for variant in all_variants
            }

            # Determine which product variants need to be created based on the attribute
            # configuration. If any attribute is set to generate variants dynamically, skip the
            # process.
            # Technical note: if there is no attribute, a variant is still created because
            # 'not any([])' and 'set([]) not in set([])' are True.
            if not tmpl_id.has_dynamic_attributes():
                # Iterator containing all possible `product.template.attribute.value` combination
                # The iterator is used to avoid MemoryError in case of a huge number of combination.
                all_combinations = itertools.product(*[
                    ptal.product_template_value_ids._only_active() for ptal in lines_without_no_variants
                ])
                # For each possible variant, create if it doesn't exist yet.
                for combination_tuple in all_combinations:
                    combination = self.env['product.template.attribute.value'].concat(*combination_tuple)
                    if combination in existing_variants:
                        current_variants_to_activate += existing_variants[combination]
                    else:
                        current_variants_to_create.append({
                            'product_tmpl_id': tmpl_id.id,
                            'product_template_attribute_value_ids': [(6, 0, combination.ids)],
                            'active': tmpl_id.active,
                        })
                        if len(current_variants_to_create) > 1000:
                            raise UserError(_(
                                'The number of variants to generate is too high. '
                                'You should either not generate variants for each combination or generate them on demand from the sales order. '
                                'To do so, open the form view of attributes and change the mode of *Create Variants*.'))
                variants_to_create += current_variants_to_create
                # add condition only active product.template that will add to variant activation
                if tmpl_id.active:
                    variants_to_activate += current_variants_to_activate

            else:
                for variant in existing_variants.values():
                    is_combination_possible = self._is_combination_possible_by_config(
                        combination=variant.product_template_attribute_value_ids,
                        ignore_no_variant=True,
                    )
                    if is_combination_possible:
                        current_variants_to_activate += variant
                # add condition only active product.template that will add to variant activation
                if tmpl_id.active:
                    variants_to_activate += current_variants_to_activate

            variants_to_unlink += all_variants - current_variants_to_activate

        if variants_to_activate:
            variants_to_activate.write({'active': True})
        if variants_to_create:
            Product.create(variants_to_create)
        if variants_to_unlink:
            variants_to_unlink._unlink_or_archive()

        # prefetched o2m have to be reloaded (because of active_test)
        # (eg. product.template: product_variant_ids)
        # We can't rely on existing invalidate_cache because of the savepoint
        # in _unlink_or_archive.
        self.flush()
        self.invalidate_cache()
        return True

    def action_approve_product(self):
        view_id = self.env.ref('bs_sarinah_product.form_wizard_product_approval').id
        return {
            'name': 'Product Approval',
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.product.approval',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'new',
            'context': {
                'product_tmpl_ids': self.ids,
            }
        }

    # @api.onchange('is_coupon')
    # def _onchange_is_coupon(self):
    #     if self.is_coupon and not self.categ_id.is_for_coupon:
    #         categ_id = self.categ_id.search([('is_for_coupon', '=', True)], limit=1)
    #         self.categ_id = categ_id.id or False
    #     if not self.is_coupon and self.categ_id.is_for_coupon:
    #         self.categ_id = False

    # hs
    @api.onchange('is_coupon')
    def _onchange_is_coupon(self):
        if self.is_coupon and not self.categ_id.is_for_coupon:
            old_categ_id = self.categ_id.id or False
            categ_id = self.categ_id.search([('is_for_coupon', '=', True)], limit=1)
            self.categ_id = categ_id.id or old_categ_id
        if not self.is_coupon and self.categ_id.is_for_coupon:
            old_categ_id = self.categ_id.id or False
            self.categ_id = old_categ_id