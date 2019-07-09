# -*- coding: utf-8 -*-

from odoo import fields, models, api

class ProductNotes(models.Model):
    _name = 'product.notes'

    product_id = fields.Many2one('product.product', string='Product')
    partner_id = fields.Many2one('res.partner', string='Customer')
    notes = fields.Text(string='Notes')

ProductNotes()
