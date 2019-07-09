# -*- coding: utf-8 -*-

from odoo import models, fields, api,_


class PriceMaintanacePricelist(models.TransientModel):

    _name = 'price.maintanace.customer.pricelist'

    pricelist_id = fields.Many2one('product.pricelist', string='Price List')
    product_id = fields.Many2one('product.product', string='Product')
    price = fields.Float('Price')
    partner_id = fields.Many2one('res.partner' , string='Customer')
    sale_uoms = fields.Many2many('product.uom', string='Sale UOMS')
    product_uom = fields.Many2one('product.uom', string='Unit Of Measure', domain="[('id', 'in', sale_uoms)]")
    customer_pricelist_id = fields.Many2one('customer.product.price')
    price_edit_id = fields.Many2one('price.maintanace.edit' , string='Price Maintanace Edit')


PriceMaintanacePricelist()

class VendorPricelist(models.TransientModel):

    _name = 'vendor.price.edit'

    edit_id = fields.Many2one('price.maintanace.edit' , string='Price Maintanace Edit')
    cost_change_id = fields.Many2one('cost.change' , string='Cost Change')
    price_filter = fields.Selection([('percentage', '%'), ('fixed', 'Fixed Amount')], string='Increase Cost by')
    run_date = fields.Date('Update Date')
    price_change = fields.Float(string='Cost Change')




VendorPricelist()



class PriceMaintanace(models.TransientModel):

    _name = 'price.maintanace.edit'
    _description = "Price Maintanace Edit Wizard"

    lst_price = fields.Float(string='Standard Price')
    standard_price = fields.Float(string='Cost')
    product_id = fields.Many2one('product.product', string='Product')
    future_price_ids = fields.One2many('vendor.price.edit', 'edit_id', string='Future Purchase Price')
    customer_price_ids = fields.One2many('price.maintanace.customer.pricelist', 'price_edit_id', string='Customer price list')
    note = fields.Text('Note')

    @api.multi
    def edit_prices(self):
        note = ''
        product = self.product_id
        if product.lst_price != self.lst_price:
            note = note + '\nSale price changed %s to %s'%(product.lst_price, self.lst_price)
            product.lst_price = self.lst_price
        if product.standard_price != self.standard_price:
            note = note + '\nCost changed %s to %s'%(product.standard_price, self.standard_price)
            product.standard_price = self.standard_price

        for customer_price in self.customer_price_ids:
            if customer_price.price != customer_price.customer_pricelist_id.price:
                note = note + '\n %s - price(%s) changed %s to %s'%(customer_price.pricelist_id.name, customer_price.product_uom.name, customer_price.customer_pricelist_id.price, customer_price.price)

                customer_price.customer_pricelist_id.price = customer_price.price

        for future_price in self.future_price_ids:
            if future_price.price_change != future_price.cost_change_id.price_change:
                note = note + '\nFuture Price changed %s to %s'%(future_price.cost_change_id.price_change, future_price.price_change)
                future_price.cost_change_id.price_change = future_price.price_change
        if note or self.note:
            note = note + '\nNote :\n' + self.note
            self.env['price.edit.notes'].create({
                                                'product_id': self.product_id.id,
                                                'edit_date': fields.Datetime.now(),
                                                'note': note,
                                                'user_id': self.env.user.id
                                                })

    @api.model
    def default_get(self, fields):
        res = super(PriceMaintanace, self).default_get(fields)
        if self._context.get('product_id'):
            res['product_id'] = self._context['product_id']
            res['lst_price'] = self._context['lst_price'] and self._context['lst_price'] or 0.0
            res['standard_price'] = self._context['cost'] and self._context['cost'] or 0.0
            if self._context['customer_pricelist']:
                price_lists = []
                for id in self._context['customer_pricelist']:
                    record = self.env['customer.product.price'].browse(id)
                    value = {
                            'price': record.price,
                            'pricelist_id': record.pricelist_id.id,
                            'partner_id': record.partner_id.id,
                            'customer_pricelist_id': record.id,
                            'product_uom': record.product_uom.id,
                            'sale_uoms':record.sale_uoms.ids
                             }
                    price_lists.append((0, 0, value))
                res['customer_price_ids'] = price_lists
            if self._context['future_price']:
                future_price = []
                for id in self._context['future_price']:
                    record = self.env['cost.change'].browse(id)
                    value = {
                            'price_filter': record.price_filter,
                            'run_date': record.run_date,
                            'price_change': record.price_change,
                            'cost_change_id': record.id
                             }
                    future_price.append((0, 0, value))
                res['future_price_ids'] = future_price

        return res

PriceMaintanace()
