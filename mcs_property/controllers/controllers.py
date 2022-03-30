# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.exceptions import UserError
from odoo.http import request


class McsPropertySignup(AuthSignupHome):
    def _signup_with_values(self, token, values):
        db, login, password = request.env['res.users'].sudo().signup(values, token)

        request.env.cr.commit()     # as authenticate will use its own cursor we need to commit the current transaction

        uid = request.session.authenticate(db, login, password)

        company = request.env['res.partner'].sudo().search([
                ('npwp', '=', request.params['npwp_company']),
                ('is_company', '=', True),
            ], limit=1)
        partner = request.env['res.partner'].sudo().search([
                ('name', '=', request.params['name']),
                ('email', '=', request.params['login']),
            ], limit=1)

        if partner:
            partner.sudo().write({
                'parent_id': company.id,
            })
        else:
            request.env['res.partner'].create({
                                'user_id': uid,
                                'name': request.params['name'],
                                'email': request.params['login'],
                                'parent_id': company.id,
                            })

        if not uid:
            raise SignupError(_('Authentication Failed.'))

    def do_signup(self, qcontext):
        """ Shared helper that creates a res.partner out of a token """
        values = { key: qcontext.get(key) for key in ('login', 'name', 'password') }
        if not values:
            raise UserError(_("The form was not properly filled in."))
        if values.get('password') != qcontext.get('confirm_password'):
            raise UserError(_("Passwords do not match; please retype them."))

        company = request.env['res.partner'].sudo().search([
                ('npwp', '=', qcontext.get('npwp_company')),
                ('is_company', '=', True),
            ], limit=1)

        if company:
            # values['company_id'] = company.id
            supported_lang_codes = [code for code, _ in request.env['res.lang'].get_installed()]
            lang = request.context.get('lang', '')
            if lang in supported_lang_codes:
                values['lang'] = lang
            self._signup_with_values(qcontext.get('token'), values) 
            request.env.cr.commit()   
        else:
            raise UserError(_("NPWP Perusahaan tidak terdaftar"))