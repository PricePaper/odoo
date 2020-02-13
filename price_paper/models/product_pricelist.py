# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from datetime import datetime


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'


    type = fields.Selection(string='Type', selection=[('customer', 'Customer'), ('shared', 'Shared'), ('competitor', 'Competitor')])
    customer_pricelist_ids = fields.One2many('customer.pricelist', 'pricelist_id')
    customer_product_price_ids = fields.One2many('customer.product.price', 'pricelist_id')
    expiry_date = fields.Date('Valid Upto')
    price_lock = fields.Boolean(string='Price Change Lock', default=False)
    lock_expiry_date = fields.Date(string='Lock Expiry date')
    partner_id = fields.Many2one('res.partner', string='Customer', store=True, compute='_compute_partner')

    @api.depends('customer_product_price_ids.partner_id')
    def _compute_partner(self):
        for pricelist in self:
            if pricelist.type == 'customer':
                pricelist.partner_id = pricelist.customer_product_price_ids and pricelist.customer_product_price_ids[0].partner_id.id or False

    @api.model
    def _cron_update_price_change_lock(self):
        domain = [('price_lock', '=', True), ('lock_expiry_date', '<', datetime.today())]
        pricelists = self.search(domain)
        product_prices = self.env['customer.product.price'].search(domain)
        vals = {
            'price_lock': False,
            'lock_expiry_date': False
        }
        pricelists.write(vals)
        product_prices.write(vals)


ProductPricelist()
