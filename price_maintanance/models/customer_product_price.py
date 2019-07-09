# -*- coding: utf-8 -*-

from odoo import fields, models, api
from datetime import datetime

class CustomerProductPrice(models.Model):
    _inherit = 'customer.product.price'


    customer_rank = fields.Char(string='Customer Rank', related='partner_id.rnk_lst_3_mon', readonly=True)
    mrg_per_lst_3_mon = fields.Float(string='Profit Margin %', related='partner_id.mrg_per_lst_3_mon', readonly=True)
    last_sale_date = fields.Datetime(compute='_get_last_sale_details', string='Last Sale', readonly=True)
    last_sale_price = fields.Float(compute='_get_last_sale_details', string='Last Sale Price', readonly=True)
    last_quantity_sold = fields.Float(compute='_get_last_sale_details', string='Last Sale Qty', readonly=True)
    median_price = fields.Html(string='Median Prices', related='product_id.median_price', readonly=True)
    competietor_price_ids = fields.Many2many('customer.product.price', compute="_get_competietor_prices", string='Competietor Price Entries')
    std_price = fields.Float(string='Standard Price', related='product_id.lst_price', readonly=True)
    deviation = fields.Float(string='Deviation', compute="get_deviation", readonly=True)

    @api.depends('price','std_price')
    def get_deviation(self):
        for line in self:
            line.deviation = line.price - line.std_price

    @api.multi
    def _get_competietor_prices(self):
        for line in self:
            comp_lines = self.search([('pricelist_id.type', '=', 'competitor'), ('product_id', '=', line.product_id.id)])
            line.competietor_price_ids = [l.id for l in comp_lines]




    @api.depends('partner_id', 'product_id')
    def _get_last_sale_details(self):
        for record in self:
            res = {}
            pr_id = record.product_id.id
            if not isinstance(pr_id, int):
                record_read = record.search_read([('id', '=', record.id)], ['product_id'])
                pr_id = record_read and record_read[0].get('product_id', ()) and record_read[0].get('product_id', ())[0]
            if record.pricelist_id.type != 'customer':
                continue
            self._cr.execute("""select so.confirmation_date, sol.price_unit, sol.product_uom_qty from sale_order_line sol join sale_order so  ON (so.id = sol.order_id) where so.state in ('sale', 'done') and so.partner_id=%s and sol.product_id=%s order by so.confirmation_date desc limit 1""" % (record.partner_id.id, pr_id))
            res = self._cr.dictfetchall()
            if res and res[0]:
                record.last_sale_date = res[0].get('confirmation_date', '')
                record.last_sale_price = res[0].get('price_unit', '')
                record.last_quantity_sold = res[0].get('product_uom_qty', '')

CustomerProductPrice()




