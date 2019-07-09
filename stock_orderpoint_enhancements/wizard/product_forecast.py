# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import models, fields, api



class ProductForecast(models.TransientModel):
    _name = 'product.forecast'
    _description = 'Show product Forecast'
    _order = 'date desc'


    date = fields.Date(string='Date')
    product_id = fields.Many2one('product.product', string="Product")
    quantity = fields.Float(string="Product Quantity")
    quantity_max = fields.Float(string="Product Quantity Max")
    quantity_min = fields.Float(string="Product Quantity Min")



ProductForecast()
