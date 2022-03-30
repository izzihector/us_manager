# -*- coding: utf-8 -*-
# Copyright 2019 Bumiswa

from collections import OrderedDict
import base64, json

from odoo import _
from odoo.http import request, route
from odoo.tools.safe_eval import safe_eval
from odoo.osv.expression import OR

from odoo.addons.vendor_portal_management.controllers.main import CustomerPortal
from odoo.addons.portal.controllers.portal import get_records_pager, pager as portal_pager


class CustomerPortal(CustomerPortal):

    def _prepare_product(self, product_id):
        values = super(CustomerPortal, self)._prepare_product(product_id)
        values.update({'attributes': request.env['product.attribute'].search([
            ('id', 'not in', values['vendor_product'].attribute_line_ids.mapped('attribute_id').ids),
        ])})
        return values

    def _get_low_stock_products(self, domain, order="product_name", limit=False, offset=0):
        product_obj = request.env['vendor.product']
        stock_quant_obj = request.env['stock.quant']
        location_obj = request.env['vendor.location']

        values = []
        for product_id in product_obj.search(domain, order=order, limit=limit, offset=offset).mapped('product_variant_ids'):
            lines = []
            for location_id in location_obj.search([]):
                stock_at_location = stock_quant_obj._get_available_quantity(product_id.sudo().product_id, location_id.sudo().location_id, allow_negative=True)
                if stock_at_location < product_id.minimum_quantity:
                    lines.append({
                        'location_id': location_id,
                        'current_stock': stock_at_location,
                    })
            if len(lines):
                values.append({
                    'product_id': product_id,
                    'lines': lines
                })
        return values

    """
    Overwritting the controller to add vendor pages, forms and menus
    """
    def _prepare_portal_layout_values(self):
        """
        Overwrite to pass new params such as configured options

        Returns:
         * dict

        Extra info:
         * we do not include archived products to count
        """
        values = super(CustomerPortal, self)._prepare_portal_layout_values()
        ICPSudo = request.env['ir.config_parameter'].sudo()
        vendor_portal_stocks = safe_eval(ICPSudo.get_param('show_stocks_in_portal', "False"))
        vendor_product = request.env['vendor.product']
        vendor_location = request.env['vendor.location']
        vendor_stock_picking = request.env['vendor.stock.picking']
        sales_report = request.env['sale.report']
        com_partner = request.env.user.partner_id.commercial_partner_id
        responsible_user = request.env.user.partner_id.user_id or com_partner.user_id
        products_count = vendor_product.search_count([
            ("partner_id", "child_of", com_partner.id),
        ])
        locations_count = vendor_location.search_count([
            ("partner_id", "child_of", com_partner.id),
        ])
        delivery_order_count = vendor_stock_picking.search_count([
            ("partner_id", "child_of", com_partner.id),
            ("operation_type", "=", "incoming"),
        ])
        outgoing_do_count = vendor_stock_picking.search_count([
            ("partner_id", "child_of", com_partner.id),
            ("operation_type", "=", "outgoing"),
        ])
        sales_report_count = sales_report.sudo().search_count([
            ("product_id.owner_id", "child_of", com_partner.id),
        ])
        domain = [
            ("partner_id", "child_of", com_partner.id),
            "|",
                ("active", "=", True),
                ("active", "=", False),
        ]
        low_stock_product_count = len(self._get_low_stock_products(domain))
        values.update({
            "products_count": products_count,
            "vendor_portal_stocks": vendor_portal_stocks,
            "locations_count": locations_count,
            "responsible_user": responsible_user,
            "delivery_order_count": delivery_order_count,
            "outgoing_do_count": outgoing_do_count,
            "low_stock_product_count": low_stock_product_count,
            "sales_report_count": sales_report_count,
        })
        return values

    # override to remove domain
    def _prepare_vals_locations(self, page=1, sortby=None, filterby=None, search=None, search_in='all', **kw):
        """
        The method to prepare values for locations list

        Returns:
         * dict
        """
        url="/my/locations"
        values = self._prepare_locations_helper(page=page, sortby=sortby, filterby=filterby, search=search,
                                                search_in=search_in, url=url, **kw)
        values.update({
            'page_name': _('My Locations'),
            'default_url': '/my/locations',
        })
        request.session['all_locations'] = values.get("location_ids").ids[:100]
        return values

    def _return_search_in_low_stock_products(self, search_in, search):
        """
        The method to construct domain based on current user search

        Returns:
         * list - domain to search
        """
        search_domain = []
        if search_in in ('product_name', 'all'):
            search_domain = OR([search_domain, [('product_name', 'ilike', search)]])
        if search_in in ('product_code', 'all'):
            search_domain = OR([search_domain, [('product_code', 'ilike', search)]])
        return search_domain

    def _return_searchbar_sortings_low_stock_products(self, values):
        """
        Returns:
         * dict
            ** search_by_sortings - {}
            ** searchbar_filters dict - {}
            ** searchbar_inputs - {}

        Returns:
         * dict
        """
        searchbar_sortings = {
            'v_name': {'label': _('Name'), 'order': 'product_name asc, id desc'},
            'v_code': {'label': _('Code'), 'order': 'product_code asc, id desc'},
        }
        searchbar_filters = {
            'all': {'label': _('All'), 'domain': ['|', ('active', '=', True), ('active', '=', False)]},
            'active': {'label': _("Active"), 'domain': [('active', '=', True)]},
            'archived': {'label': _("Archived"), 'domain': [('active', '=', False)]},

        }
        if values.get("vendor_portal_stocks"):
            searchbar_filters.update({
                'out_of_stock':
                    {'label': _("Out of Stock"), 'domain': [('zero_qty', '=', True), ('active', '=', True)]},
            })
        searchbar_inputs = {
            'name': {'input': 'product_name', 'label': _('Search by name')},
            'code': {'input': 'product_code', 'label': _('Search by code')},
            'all': {'input': 'all', 'label': _('Search in all')},
        }
        return {
            "searchbar_sortings": searchbar_sortings,
            "searchbar_filters": searchbar_filters,
            "searchbar_inputs": searchbar_inputs,
        }

    def _prepare_low_stock_products_helper(self, page=1, sortby=None, filterby=None, search=None, search_in='content', domain=[],
                                 url="/my/low_stock_products", **kw):
        """
        The helper method for products list

        Returns:
         * dict
        """
        values = self._prepare_portal_layout_values()
        product_object = request.env['vendor.product']
        if not sortby:
            sortby = 'v_name'
        if not filterby:
            filterby = 'active'
        searches_res = self._return_searchbar_sortings_low_stock_products(values)
        searchbar_sortings = searches_res.get("searchbar_sortings")
        searchbar_filters = searches_res.get("searchbar_filters")
        searchbar_inputs = searches_res.get("searchbar_inputs")
        sort_order = searchbar_sortings[sortby]['order']
        domain += searchbar_filters[filterby]['domain']
        if search and search_in:
            search_domain = self._return_search_in_low_stock_products(search_in, search)
            domain += search_domain
        products_count_count = product_object.search_count(domain)
        pager = portal_pager(
            url=url,
            url_args={
                'sortby': sortby,
                'filterby': filterby,
                'search': search,
                'search_in': search_in,
            },
            total=products_count_count,
            page=page,
            step=self._items_per_page,
        )
        low_stocks = self._get_low_stock_products(
            domain,
            order=sort_order,
            limit=self._items_per_page,
            offset=pager['offset']
        )
        values.update({
            'low_stocks': low_stocks,
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'searchbar_inputs': searchbar_inputs,
            'search_in': search_in,
            'sortby': sortby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
        })
        return values

    def _prepare_vals_low_stock_products(self, page=1, sortby=None, filterby=None, search=None, search_in='all', **kw):
        """
        The method to prepare values for products list

        Returns:
         * dict
        """
        domain = [
            ("partner_id", "child_of", request.env.user.partner_id.commercial_partner_id.id),
            "|",
                ("active", "=", True),
                ("active", "=", False),
        ]
        url="/my/low_stock_products"
        values = self._prepare_low_stock_products_helper(page=page, sortby=sortby, filterby=filterby, search=search,
                                               search_in=search_in, domain=domain, url=url, **kw)
        values.update({
            'page_name': _('Low Stock Products'),
            'default_url': '/my/low_stock_products',
        })
        request.session['all_products'] = [low_stock.get('product_id').id for low_stock in values.get('low_stocks')][:100]
        return values

    @route(['/my/low_stock_products', '/my/low_stock_products/page/<int:page>',], type='http', auth="user", website=True)
    def vendor_low_stock_product_list(self, page=1, sortby=None, filterby=None, search=None, search_in='all', **kw):
        """
        The route to open the list of vendor low stock products
        """
        values = self._prepare_vals_low_stock_products(page=page, sortby=sortby, filterby=filterby, search=search,
                                             search_in=search_in, **kw)
        res = request.render("bs_sarinah_portal.vendor_low_stock_product_list", values)
        return res

    @route([
        '/my/delivery_orders',
        '/my/delivery_orders/<string:operation_type>',
        '/my/delivery_orders/<string:operation_type>/page/<int:page>',
        '/my/delivery_orders/page/<int:page>',
    ], type='http', auth="user", website=True)
    def vendor_delivery_order_list(self, operation_type="incoming", page=1, sortby='v_name', filterby='all', search=None, search_in='all', **kw):
        """
        The route to open the list of vendor products
        """
        # Pre defined values.
        url="/my/delivery_orders"
        values = self._prepare_portal_layout_values()
        picking_obj = request.env['vendor.stock.picking']

        # Main domain. This domain wi always included in any searches.
        domain = [
            ("partner_id", "child_of", request.env.user.partner_id.commercial_partner_id.id),
            ("operation_type", "=", operation_type),
        ]

        # Definitions of sorting and filtering options and the representative rules.
        searchbar_sortings = {
            'v_name': {'label': _('Reference'), 'order': 'name asc, id desc'},
            'v_ref': {'label': _('Internal References'), 'order': 'vendor_reference asc, id desc'},
            'v_loc': {'label': _('Locations'), 'order': 'vendor_location_id asc, id desc'},
        }
        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
            'draft': {'label': _("Draft"), 'domain': [('state', '=', 'draft')]},
            'validate': {'label': _("Validated"), 'domain': [('state', '=', 'validate')]},

        }
        searchbar_inputs = {
            'name': {'input': 'name', 'label': _('Search by reference')},
            'loc': {'input': 'vendor_location_id', 'label': _('Search by locations')},
            'ref': {'input': 'vendor_reference', 'label': _('Search by internal references')},
            'all': {'input': 'all', 'label': _('Search in all')},
        }

        # Get selected sorting and filters.
        sort_order = searchbar_sortings[sortby]['order']
        domain += searchbar_filters[filterby]['domain']
        if search and search_in:
            search_domain = []
            if search_in in ('name', 'all'):
                search_domain = OR([search_domain, [('name', 'ilike', search)]])
            if search_in in ('vendor_reference', 'all'):
                search_domain = OR([search_domain, [('vendor_reference', 'ilike', search)]])
            if search_in in ('vendor_location_id', 'all'):
                search_domain = OR([search_domain, [('vendor_location_id', 'ilike', search)]])
            domain += search_domain

        # Define portal pager for paginations.
        picking_count = picking_obj.search_count(domain)
        pager = portal_pager(
            url=url,
            url_args={
                'sortby': sortby,
                'filterby': filterby,
                'search': search,
                'search_in': search_in,
            },
            total=picking_count,
            page=page,
            step=self._items_per_page,
        )

        # Define page values for rendering.
        picking_ids = picking_obj.search(
            domain,
            order=sort_order,
            limit=self._items_per_page,
            offset=pager['offset']
        )
        values.update({
            'picking_ids': picking_ids,
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'searchbar_inputs': searchbar_inputs,
            'search_in': search_in,
            'sortby': sortby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
            'page_name': _('Delivery Orders'),
            'default_url': url,
            'operation_type': operation_type,
        })
        
        # Set session value. i don't know why.
        request.session['all_pickings'] = [picking_ids.ids][:100]

        # Render page with defined values
        res = request.render("bs_sarinah_portal.vendor_stock_picking_list", values)
        return res

    @route(['/my/delivery_orders/<int:rec_id>'], type='http', auth="user", website=True)
    def vendor_delivery_order_detail(self, rec_id, sortby='v_name', filterby='all', search=None, search_in='all', **kw):
        values = {}
        values['picking'] = request.env['vendor.stock.picking'].browse(rec_id)
        res = request.render("bs_sarinah_portal.vendor_stock_picking_detail", values)
        return res

    @route(['/my/product_variants/<int:rec_id>'], type='http', auth="user", website=True)
    def vendor_product_variant_detail(self, rec_id, **kw):
        values = {}
        values['variant'] = request.env['vendor.product.variant'].browse(rec_id)
        res = request.render("bs_sarinah_portal.vendor_product_variant_detail", values)
        return res

    @route([
        '/my/sales_report',
        '/my/sales_report/page/<int:page>',
    ], type='http', auth="user", website=True)
    def vendor_sales_report_list(self, page=1, sortby='v_default', filterby='all', search=None, search_in='all', **kw):
        """
        The route to open the list of sales report
        """
        # Pre defined values.
        url="/my/sales_report"
        values = self._prepare_portal_layout_values()
        # picking_obj = request.env['vendor.stock.picking']
        report_obj = request.env['sale.report']

        # Main domain. This domain wi always included in any searches.
        domain = [
            ("product_id.owner_id", "child_of", request.env.user.partner_id.commercial_partner_id.id),
        ]

        # Definitions of sorting and filtering options and the representative rules.
        searchbar_sortings = {
            'v_default': {'label': _('Default'), 'order': 'date desc, branch_id asc, brand_id asc, product_id asc, id desc'},
            'v_location': {'label': _('Location'), 'order': 'branch_id asc, id desc'},
            'v_brand': {'label': _('Brand'), 'order': 'brand_id asc, id desc'},
            'v_product': {'label': _('Product'), 'order': 'product_id asc, id desc'},
        }
        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
            'draft': {'label': _("Draft"), 'domain': [('state', '=', 'draft')]},
            'sale': {'label': _("Sale Order"), 'domain': [('state', '=', 'sale')]},
            'paid': {'label': _("Paid"), 'domain': [('state', '=', 'paid')]},

        }
        searchbar_inputs = {
            'product': {'input': 'product_id', 'label': _('Search by product')},
            'brand': {'input': 'brand_id', 'label': _('Search by brand')},
            'location': {'input': 'branch_id', 'label': _('Search by location')},
            'all': {'input': 'all', 'label': _('Search in all')},
        }

        # Get selected sorting and filters.
        sort_order = searchbar_sortings[sortby]['order']
        domain += searchbar_filters[filterby]['domain']
        if search and search_in:
            search_domain = []
            if search_in in ('product_id', 'all'):
                search_domain = OR([search_domain, [('product_id', 'ilike', search)]])
            if search_in in ('brand_id', 'all'):
                search_domain = OR([search_domain, [('brand_id', 'ilike', search)]])
            if search_in in ('branch_id', 'all'):
                search_domain = OR([search_domain, [('branch_id', 'ilike', search)]])
            domain += search_domain

        # Define portal pager for paginations.
        sales_report_count = report_obj.sudo().search_count(domain)
        pager = portal_pager(
            url=url,
            url_args={
                'sortby': sortby,
                'filterby': filterby,
                'search': search,
                'search_in': search_in,
            },
            total=sales_report_count,
            page=page,
            step=self._items_per_page,
        )

        # Define page values for rendering.
        report_ids = report_obj.sudo().search(
            domain,
            order=sort_order,
            limit=self._items_per_page,
            offset=pager['offset']
        )
        values.update({
            'report_ids': report_ids,
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'searchbar_inputs': searchbar_inputs,
            'search_in': search_in,
            'sortby': sortby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
            'page_name': _('Sales Report'),
            'default_url': url,
        })

        # Set session value. i don't know why.
        request.session['all_sales_report_ids'] = [report_ids.ids][:100]

        # Render page with defined values
        res = request.render("bs_sarinah_portal.vendor_sales_report_list", values)
        return res
