# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class AccountAccount(models.Model):
    _inherit = 'account.account'

    is_driver_writeoff_account = fields.Boolean(string='Driver Writeoff Account', help='Check this box if this is the driver writeoff account.')

AccountAccount()
