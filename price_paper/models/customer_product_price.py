# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from datetime import datetime, date
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta

class CustomerProductPrice(models.Model):
    _name = 'customer.product.price'
    _description = 'Customer Pricelist Product Price'

    pricelist_id = fields.Many2one('product.pricelist', string='Price List')
    product_id = fields.Many2one('product.product', string='Product')
    price = fields.Float(string='Price')
    partner_id = fields.Many2one('res.partner' , string='Customer', compute='_compute_partner', store=False)
    sale_uoms = fields.Many2many(related='product_id.sale_uoms', string='Sale UOMS')
    product_uom = fields.Many2one('uom.uom', string='Unit Of Measure', domain="[('id', 'in', sale_uoms)]")
    price_last_updated = fields.Date(string='Price last updated', default=date.today(), readonly=True)
    price_lock = fields.Boolean(string='Price Change Lock', default=False)
    lock_expiry_date = fields.Date(string='Lock Expiry date')
    currency_id = fields.Many2one(related="product_id.currency_id", readonly=True)

    @api.depends('pricelist_id')
    def _compute_partner(self):
        for rec in self:
            if rec.pricelist_id and rec.pricelist_id.type == 'customer':
                partner_id = rec.pricelist_id.mapped('partner_ids')
                if partner_id and len(partner_id) == 1:
                    rec.partner_id = partner_id.id



    # _sql_constraints = [
    #     ('pricelist_product_uom_uniq', 'UNIQUE (pricelist_id, product_id, product_uom)',
    #      'Combination of Product and product UOM must be unique'),
    # ]

    @api.multi
    @api.constrains('pricelist_id', 'product_id', 'product_uom')
    def _check_unique_constrain(self):
        for rec in self:
            if rec.pricelist_id and rec.product_id and rec.product_uom:
                result = rec.pricelist_id.customer_product_price_ids.filtered(
                    lambda r: r.product_id.id == rec.product_id.id and
                    r.product_uom.id == rec.product_uom.id and r.id != rec.id)
                if result:
                    raise ValidationError(
                    _('Already a record with same product and same UOM exists in Pricelist'))


    @api.multi
    def write(self, vals):
        """
        overriden to update price_last_updated
        """
        if 'price' in vals:
            log_vals = {'change_date' : fields.Datetime.now(),
                        'type': 'pricelist_price',
                        'old_price': self.price,
                        'new_price': vals.get('price'),
                        'user_id': self.env.user.id,
                        'uom_id': self.product_uom.id,
                        'pricelist_id':self.pricelist_id and self.pricelist_id.id,
                        'product_id': self.product_id.id
                        }
            if self._context.get('user', False):
                log_vals['user_id'] = self._context.get('user', False)
            # if self._context.get('from_cron', False):
            #     log_vals['user_id'] = False
            self.env['product.price.log'].create(log_vals)
            vals['price_last_updated'] = date.today()
        result = super(CustomerProductPrice, self).write(vals)
        return result

    @api.model
    def create(self, vals):
        res = super(CustomerProductPrice, self).create(vals)
        if 'price' in vals:
            log_vals = {'change_date' : fields.Datetime.now(),
                        'type': 'pricelist_price',
                        'new_price': vals.get('price'),
                        'user_id': self.env.user.id,
                        'uom_id': res.product_uom.id,
                        'pricelist_id':res.pricelist_id and self.pricelist_id.id,
                        'product_id': res.product_id.id
                        }
            if self._context.get('user', False):
                log_vals['user_id'] = self._context.get('user', False)
            self.env['product.price.log'].create(log_vals)
        return res

    @api.multi
    @api.depends('pricelist_id', 'product_id', 'partner_id')
    def name_get(self):
        result = []
        for record in self:
            name = "%s_%s_%s_%s" % (record.pricelist_id and record.pricelist_id.name or '', record.product_id and record.product_id.name or '', record.product_uom and record.product_uom.name or '', record.partner_id and record.partner_id.name or '')
            result.append((record.id,name))
        return result

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            self.product_uom = self.product_id.uom_id and self.product_id.uom_id
            uom_price = self.product_id.uom_standard_prices.filtered(lambda r: r.uom_id == self.product_id.uom_id)
            if uom_price:
                product_price = uom_price[0].price
                self.price = product_price
        else:
            self.product_uom = False
            self.price = 0.0

    @api.onchange('product_uom')
    def onchange_product_uom(self):
        if self.product_id and self.product_uom:
            uom_price = self.product_id.uom_standard_prices.filtered(lambda r: r.uom_id == self.product_uom)
            if uom_price:
                product_price = uom_price[0].price
                self.price = product_price
        else:
            self.price = 0.0

    @api.onchange('price_lock')
    def onchange_price_lock(self):
        if self.price_lock:
            if self.env.user.company_id and self.env.user.company_id.price_lock_days:
                days = self.env.user.company_id.price_lock_days
                self.lock_expiry_date =  date.today()+relativedelta(days=days)
        else:
            self.lock_expiry_date = False



CustomerProductPrice()
