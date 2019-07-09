# -*- coding: utf-8 -*-

from odoo import fields, models, api


class DeviatedCostContract(models.Model):
    _name = 'deviated.cost.contract'

    name = fields.Char(string="Contract Name")
    expiration_date = fields.Datetime(string="Expiration Date")
    partner_product_ids = fields.One2many('res.category.product.cost', 'partner_category_id', string="Products")


DeviatedCostContract()
