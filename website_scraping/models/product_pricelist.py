# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    competitor_id = fields.Many2one('website.scraping.cofig' , string='Competitor')
    competietor_margin = fields.Float(string='Competitor Margin%', help='Margin From Competitor Price. When pricelist is auto updated, this margin is considered.')

ProductPricelist()
