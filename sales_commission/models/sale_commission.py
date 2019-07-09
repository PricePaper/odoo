# -*- coding: utf-8 -*-

from odoo import fields, models, api, _

class SaleCommission(models.Model):
    _name = 'sale.commission'

    sale_person_id = fields.Many2one('res.partner', string='Sale Person')
    sale_order = fields.Char(string='Sale Order')
    commission = fields.Float(string='Commission')
    invoice_id = fields.Many2one('account.invoice', string='Invoice')
    is_paid = fields.Boolean(string='Paid')
    invoice_type = fields.Selection(selection=[('out_invoice', 'Invoice'), ('out_refund', 'Refund')], string='Invoice Type')
    invoice_amount = fields.Float(string='Amount')



SaleCommission()
