# -*- coding: utf-8 -*-

from odoo import fields, models, api


class PartnerProductCost(models.Model):
    _name = 'res.category.product.cost'

    product_id = fields.Many2one('product.product', string="Product")
    cost = fields.Float(string="Cost")
    partner_category_id = fields.Many2one('deviated.cost.contract', string="Rebate Contract")


    @api.onchange('product_id')
    def change_product(self):
        """
        Set the domain to prevent selected product
        appearing in search result
        """
        product_ids = [product.id for product in self.partner_category_id.partner_product_ids.mapped('product_id')]
        return {'domain': { 'product_id': ([('id', 'not in', product_ids)])}}

PartnerProductCost()
