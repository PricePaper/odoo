# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import models, fields, api



class ViewSalesHistoryPo(models.TransientModel):
    _name = 'view.sales.history.po'
    _description = 'View Sales History'

    _order = 'date desc'

    date = fields.Date(string='Date')
    partner_id = fields.Many2one('res.partner', string="Customer")
    product_id = fields.Many2one('product.product', string="Product")
    quantity = fields.Float(string="Product Quantity")
    uom = fields.Many2one('product.uom', string="UOM")
    sale_line_id = fields.Many2one('sale.order.line', string="Sale Line")



ViewSalesHistoryPo()
