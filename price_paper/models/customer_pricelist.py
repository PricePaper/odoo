# -*- coding: utf-8 -*-

from odoo import fields, models, api


class CustomerPricelist(models.Model):
    _name = 'customer.pricelist'


    sequence = fields.Integer(string='Sequence')
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist')
    partner_id = fields.Many2one('res.partner', string='Customer')

CustomerPricelist()
