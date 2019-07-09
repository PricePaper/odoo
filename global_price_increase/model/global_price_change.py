# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from dateutil.relativedelta import *
from datetime import datetime, date
from odoo.exceptions import ValidationError

class GlobalPriceChange(models.Model):
    _name = 'global.price.change'


    customer_filter = fields.Selection([('customer', 'Customer'), ('salesrep', 'Sales Person'), ('categ', 'Customer Category')], string='Update Cost of', default='customer')
    customer_ids = fields.Many2many('res.partner', string='Customer')
    salesrep_id = fields.Many2one('res.partner', string='Sales Person')
    customer_categ_ids = fields.Many2many('res.partner.category', string='Customer Category')
    # ranking_required = fields.Boolean(string='Customer Ranking Required')
    customer_ranking = fields.Char(string='Customer Ranking')
    product_filter = fields.Selection([('all', 'All Products'), ('vendor', 'Vendor'), ('categ', 'Product Category')], string='Products', default='all')
    vendor_id = fields.Many2one('res.partner', string='Vendor')
    product_category_ids = fields.Many2many('product.category', string='Category')
    is_exclude = fields.Boolean(string='Exclude customer by creation Date', default=True)
    exclude_date = fields.Date(string='Customer creation date', default=datetime.today() - relativedelta(months=6))
    price_change = fields.Float(string='Price Change %')
    run_date = fields.Date('Update Date', default=fields.Date.context_today)
    is_done = fields.Boolean(string='Done', copy=False, default=False)


    @api.constrains('customer_ranking')
    def check_customer_ranking(self):

        # if self.ranking_required and self.customer_ranking:
        if self.customer_ranking:
            ranking_list = self.customer_ranking.split(',')
            if not all(rank in ('A','B','C','D','E','F','Z') for rank in ranking_list):
                raise ValidationError(_('Customer ranking should be comma seperated values(eg : A,B,C).'))


    @api.multi
    def immediate_price_change(self):

        if not self.is_done:
            ctx = self.env.context.copy()
            ctx.update({'immediate': True})
            self.with_context(ctx).global_price_change_cron()
        return True


    @api.model
    def global_price_change_cron(self):

        if self._context.get('immediate'):
            recs = self
        else:
            recs = self.env['global.price.change'].search([('is_done', '!=', 'True'), ('run_date', '<=', datetime.today())])

        for rec in recs:
            partner_obj = self.env['res.partner']
            partner_to_filter = self.env['res.partner']

            product_obj = self.env['product.product']
            products_to_filter = []

            if rec.customer_filter == 'customer':
                partner_to_filter |= partner_obj.search([('id', 'in', rec.customer_ids.ids)])
            elif rec.customer_filter == 'salesrep':
                partner_to_filter |= partner_obj.search([('sales_person_ids.id', '=', rec.salesrep_id.id)])
            elif  rec.customer_filter == 'categ':
                partner_to_filter |= partner_obj.search([('category_id.id', 'in', rec.customer_categ_ids.ids)])

            # if rec.ranking_required and rec.customer_ranking and partner_to_filter:
            if rec.customer_ranking and partner_to_filter:
                ranking_list = rec.customer_ranking.split(',')
                if all(rank in ('A','B','C','D','E','F','Z') for rank in ranking_list):
                    partner_to_filter = partner_to_filter.filtered(lambda r: r.rnk_lst_12_mon in ranking_list)
                else:
                    raise ValidationError(_('Customer ranking should be comma seperated values(eg : A,B,C or A).'))

            customer_price_lists = self.env['customer.product.price'].search([('partner_id', 'in', partner_to_filter.ids)])

            if rec.product_filter == 'vendor':
                products_to_filter = product_obj.search([('seller_ids', '!=', False)]).filtered(lambda r: r.seller_ids[0].name.id == rec.vendor_id.id)
            elif rec.product_filter == 'categ':
                products_to_filter = product_obj.search([('categ_id', 'in', rec.product_category_ids.ids)])

            if products_to_filter:
                customer_price_lists = customer_price_lists.filtered(lambda r: r.product_id.id in products_to_filter.ids)

            if rec.is_exclude and rec.exclude_date:
                customer_price_lists = customer_price_lists.filtered((lambda r: r.partner_id.create_date < rec.exclude_date))

            today = date.today()
            for price_list in customer_price_lists:

                # skips the update pricelist if expiry lock is active and lock expiry date is set
                if price_list.price_lock and price_list.lock_expiry_date > str(today):
                    continue

                # skips the update pricelist if expiry lock is active and lock expiry date is set for the parent pricelist itself
                if price_list.pricelist_id and price_list.pricelist_id.price_lock and price_list.pricelist_id.lock_expiry_date > str(today):
                    continue

                price_list.price = price_list.price*((100+rec.price_change)/100)

            rec.is_done = True

    @api.multi
    @api.depends('run_date')
    def name_get(self):
        result = []
        for record in self:
            name = "%s" % (record.run_date)
            result.append((record.id,name))
        return result



GlobalPriceChange()
