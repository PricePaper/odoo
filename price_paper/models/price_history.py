# -*- coding: utf-8 -*-

from odoo import fields, models, api

class PriceHistory(models.Model):
    _name = 'customer.price.history'

    partner_id = fields.Many2one('res.partner', string='Customer')
    product_id = fields.Many2one('product.product', string='Product')
    product_uom_id = fields.Many2one('product.uom', string='Unit Of Measurement')
    order_line_id = fields.Many2one('sale.order.line', string='Sale order Line')
    order_id = fields.Many2one(related='order_line_id.order_id', string='Sale Order')
    order_date = fields.Datetime(related='order_line_id.order_id.confirmation_date', string='Order Date', store=True)
    cost = fields.Float('Cost')
    is_tax_applied = fields.Boolean(string='Tax Applied')
    is_last = fields.Boolean(string='Is last Purchase Made By Customer')
    superseded = fields.Many2one(related='product_id.superseded', string="Superseded")

    @api.multi
    @api.depends('product_id', 'partner_id')
    def name_get(self):
        result = []
        for record in self:
            name = "Product:%s  UOM:%s  Date:%s" % (record.product_id and record.product_id.name or '', record.product_uom_id and record.product_uom_id.name or  '', record.order_date[0:10])
            result.append((record.id, name))
        return result


    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if not args:
            args = []
        if name:
            positive_operators = ['=', 'ilike', '=ilike', 'like', '=like']
            history = self.env['customer.price.history']
            if operator in positive_operators:
                history = self.search(['|',('product_id.name', operator, name),'|', ('product_id.default_code', operator, name),('order_date', operator, name)] + args, limit=limit)
        else:
            history = self.search(args, limit=limit)
        return history.name_get()



PriceHistory()
