# -*- coding: utf-8 -*-

from odoo import fields, models, api
from datetime import date
from odoo.exceptions import ValidationError

class CostChange(models.Model):
    _name = 'cost.change'

    item_filter = fields.Selection([('product', 'Product'), ('vendor', 'Vendor and/or Product Category')], string='Update Cost of', default='product')
    price_filter = fields.Selection([('percentage', '%'), ('fixed', 'Fix to an Amount')], string='Increase Cost as', default='fixed', help='Percentage: increase cost by percentage \n Fix to an Amount: sets the price to the specified fixed amount')
    vendor_id  = fields.Many2one('res.partner', string="Vendor")
    category_id  = fields.Many2many('product.category', string="Product Category")
    product_id = fields.Many2one('product.product', string="Product")
    price_change = fields.Float(string='Cost Change')
    is_done = fields.Boolean(string='Done', copy=False, default=False)
    run_date = fields.Date('Update Date', default=fields.Date.context_today)
    update_customer_pricelist = fields.Boolean('Update Customer Pricelist')
    update_standard_price = fields.Boolean('Update Standard Price', default=True)
    old_cost = fields.Float(compute='set_old_price', string='Old Cost', store=True)
    new_cost = fields.Float(compute='compute_new_cost', string='New Cost')
    price_difference = fields.Float(compute='compute_price_difference_percent', string="Price Difference")
    price_difference_per = fields.Float(compute='compute_price_difference_percent', string="Price Difference %")
    burden_change = fields.Float(string='Burden%')
    update_burden = fields.Boolean('Update Burden%')



    @api.depends('new_cost', 'old_cost')
    def compute_price_difference_percent(self):
        for rec in self:
            if rec.item_filter == 'product' and rec.product_id:
                rec.price_difference = rec.price_change and rec.new_cost - rec.old_cost
                rec.price_difference_per = rec.price_change and rec.old_cost and (100 * (rec.new_cost - rec.old_cost))/rec.old_cost or 0.00
            else:
                rec.price_difference = 0.00
                rec.price_difference_per = 0.00


    @api.depends('item_filter','product_id')
    def set_old_price(self):
        for rec in self:
            if rec.item_filter == 'product' and rec.product_id:
                rec.old_cost = rec.product_id.standard_price
            else:
                rec.old_cost = 0.00

    @api.onchange('update_burden', 'product_id')
    def onchange_update_burden(self):
        for rec in self:
            if rec.item_filter == 'product' and rec.update_burden and rec.product_id:
                rec.burden_change = rec.product_id.burden_percent
            else:
                rec.burden_change = 0.00

    @api.onchange('product_id', 'price_filter')
    def onchange_price_filter(self):
        for rec in self:
            if rec.price_filter == 'fixed' and rec.product_id:
                rec.price_change = rec.product_id.standard_price
            else:
                rec.price_change = 0.00


    @api.depends('old_cost','price_change','price_filter')
    def compute_new_cost(self):
        for rec in self:
            if rec.item_filter == 'product' and rec.price_change:
                if rec.price_filter == 'fixed':
                    rec.new_cost = rec.price_change
                else:
                    rec.new_cost = rec.product_id and rec.product_id.standard_price * ((100+rec.price_change)/100) or 0
            else:
                rec.new_cost == 0.00



    @api.onchange('item_filter')
    def onchange_item_filter(self):
        for rec in self:
            if not self._context.get('product_id', False):
                rec.product_id = False
            rec.vendor_id = False
            rec.category_id = False
            if rec.item_filter in ['vendor']:
                rec.price_filter = 'percentage'




    @api.onchange('product_id')
    def onchange_product_id(self):
        for rec in self:
            rec.vendor_id = False
            rec.category_id = False
            if rec.item_filter == 'product':
#                if rec.product_id:
#                    rec.price_change = rec.product_id.standard_price
                if rec.product_id and rec.product_id.seller_ids:
                    for seller in rec.product_id.seller_ids:
                        rec.vendor_id = seller.name
                if rec.product_id and rec.product_id.categ_id:
                    rec.category_id = rec.product_id.categ_id



    @api.multi
    def cost_change_method(self):

        recs = self.env['cost.change'].search([('is_done', '!=', 'True'), ('run_date', '<=', date.today())])
        product_obj = self.env['product.product']
        products_to_filter = self.env['product.product']
        for rec in recs:
            if rec.item_filter == 'product':
                products_to_filter |= product_obj.search([('id', '=', rec.product_id.id)])
            elif rec.item_filter == 'vendor':
                vendor_products = product_obj.search([('seller_ids', '!=', False)])
                vendor_products = vendor_products.filtered(lambda r: r.seller_ids[0].name.id == rec.vendor_id.id)
                products_to_filter |= vendor_products
                if rec.category_id:
                    categ_products = product_obj.search([('categ_id', 'in', rec.category_id.ids)])
                    products_to_filter = products_to_filter & categ_products

            #Update list price
            if rec.update_standard_price:
                for product in products_to_filter:
                    new_price = rec.calculate_new_price(product)
                    product.lst_price = new_price

            # Update Customer pricelist
            if rec.update_customer_pricelist:
                customer_price_lists = self.env['customer.product.price'].search([('product_id', 'in', products_to_filter.ids)]).filtered(lambda r: r.pricelist_id.type != 'competitor')
                today = date.today()
                for price_list_rec in customer_price_lists:
                    # skips the update pricelist if expiry lock is active and lock expiry date is set
                    if price_list_rec.price_lock and price_list_rec.lock_expiry_date > str(today):
                        continue

                    # skips the update pricelist if expiry lock is active and lock expiry date is set for the parent pricelist itself
                    if price_list_rec.pricelist_id and price_list_rec.pricelist_id.price_lock and price_list_rec.pricelist_id.lock_expiry_date > str(today):
                        continue

                    product = price_list_rec.product_id
                    new_price = rec.calculate_new_price(product, price_list_rec)
                    price_list_rec.price = new_price

            #Update Fixed Cost
            if rec.price_filter == 'fixed':
                products_to_filter.write({'standard_price': rec.price_change})
            else:
                for product in products_to_filter:
                    product.standard_price = product.standard_price * ((100+rec.price_change)/100)
            #Update burden%
            if rec.update_burden and rec.burden_change:
                products_to_filter.write({'burden_percent': rec.burden_change})
            rec.is_done = True
        return True

    @api.model
    def cost_change_cron(self):

        recs = self.env['cost.change'].search([('is_done', '!=', 'True'), ('run_date', '<=', date.today())])
        for rec in recs:
            rec.cost_change_method()
        return True


    def calculate_new_price(self, product, pricelist=None):
        new_price = 0
        old_list_price = product.lst_price
        old_working_cost = product.cost
        if pricelist:
            old_list_price = pricelist.price
            if product.uom_id != pricelist.product_uom:
                old_working_cost = product.uom_id._compute_price(product.cost, pricelist.product_uom) * ((100+product.categ_id.repacking_upcharge)/100)

        if old_list_price:
            margin = (old_list_price - old_working_cost) / old_list_price

            if self.price_filter == 'fixed':
                new_working_cost = self.price_change * ((100+product.burden_percent)/100)
                if self.update_burden and self.burden_change:
                    new_working_cost = self.price_change * ((100+self.burden_change)/100)
                if pricelist and product.uom_id != pricelist.product_uom:
                    new_price = (product.uom_id._compute_price(new_working_cost, pricelist.product_uom) * ((100+product.categ_id.repacking_upcharge)/100)) / (1-margin)
                else:
                    new_price = new_working_cost / (1-margin)
            else:
                new_working_cost = (product.standard_price * (100+self.price_change)/100) * ((100+product.burden_percent)/100)
                if self.update_burden and self.burden_change:
                    new_working_cost = (product.standard_price * (100+self.price_change)/100) * ((100+self.burden_change)/100)
                if pricelist and product.uom_id != pricelist.product_uom:
                    new_price = (product.uom_id._compute_price(new_working_cost, pricelist.product_uom) * ((100+product.categ_id.repacking_upcharge)/100)) / (1-margin)
                new_price = new_working_cost / (1-margin)
        return new_price


    @api.multi
    @api.depends('run_date')
    def name_get(self):
        result = []
        for record in self:
            name = "%s" % (record.run_date)
            result.append((record.id,name))
        return result

    @api.one
    @api.constrains('price_change')
    def check_if_zero_cost(self):
        if not self.price_change:
            raise ValidationError('Cost change field cannot be 0.00')


CostChange()
