# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    property_stock_location = fields.Many2one('stock.location',company_dependent=True, copy=True,
            string='Stock Location',
            help="This location will be proposed as source (sale,internal) or target (purchase,production) location for stock move for this product."\
                 "Leave empty if you want to use the location of this product category")


ProductTemplate()


class ProductCategory(models.Model):
    _inherit = 'product.category'

    property_stock_location = fields.Many2one('stock.location',company_dependent=True,
            string='Stock Location', method=True, 
            help="This location will be proposed as source (sale,internal) or target (purchase,production) location for stock moves of this category")
               
ProductCategory()

