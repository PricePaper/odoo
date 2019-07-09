# -*- coding: utf-8 -*-

from odoo import models, fields, registry, api,_


class ProductCategory(models.Model):
    _inherit = 'product.category'


    class_margin = fields.Float(string='Class Margin', help='This field is used to specify the class margin for a products category. It is visible in the sale line reports.')




ProductCategory()
