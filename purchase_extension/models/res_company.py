# -*- coding: utf-8 -*-


from odoo import models, fields, api,_


class ResCompany(models.Model):
    _inherit = 'res.company'

    purchase_writeoff_account_id = fields.Many2one('account.account', string='Purchase Writeoff Account', domain=[('deprecated', '=', False)])

ResCompany()
