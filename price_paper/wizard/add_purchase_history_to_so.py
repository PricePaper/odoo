# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import UserError


class SaleHistoryLinesWizard(models.TransientModel):

    _name = 'sale.history.lines.wizard'

    product_name = fields.Char(string='Product')
    product_uom = fields.Many2one('product.uom', string="UOM")
    product_uom_qty = fields.Float(string='Quantity')
    date_order = fields.Char(string='Order Date')
    search_wizard_id = fields.Many2one('add.purchase.history.so', string='Parent')
    price_unit = fields.Float(string='Price')
    order_line = fields.Many2one('sale.order.line', string='Sale order line')
    qty_to_be = fields.Float(string='New Qty')
    product_category = fields.Many2one('product.category', string='Product Category')

SaleHistoryLinesWizard()


class AddPurchaseHistorySO(models.TransientModel):

    _name = 'add.purchase.history.so'
    _description = "Add Purchase History to SO Line"

    search_box = fields.Char(string='Search')
    purchase_history_ids = fields.One2many('sale.history.lines.wizard', 'search_wizard_id', string="Purchase History")


    @api.onchange('search_box')
    def search_product(self):

        if self._context.get('line_ids1', False):
            lines=[]
            line_ids = self.env['sale.order.line'].browse(self._context.get('line_ids1', False))
            if self.search_box:
                for line in line_ids:
                    if self.search_box.lower() in line.product_id.display_name.lower():
                        val = {
                                 'product_uom': line.product_uom.id,
                                 'date_order': line.order_id.confirmation_date,
                                 'order_line': line.id,
                                 'qty_to_be': 0.0,
                                 'price_unit': line.price_unit,
                                 'product_uom_qty':line.product_uom_qty,
                                 'product_category': line.product_id.categ_id.id,
                                 'product_name': line.product_id.display_name
                                }
                        lines.append((0,0,val))
                self.purchase_history_ids = lines

            else:
                for line in line_ids:
                    val = {
                             'product_uom': line.product_uom.id,
                             'date_order': line.order_id.confirmation_date,
                             'order_line': line.id,
                             'qty_to_be': 0.0,
                             'price_unit': line.price_unit,
                             'product_uom_qty':line.product_uom_qty,
                             'product_category': line.product_id.categ_id.id,
                             'product_name': line.product_id.display_name
                            }
                    lines.append((0,0,val))
                self.purchase_history_ids = lines




    @api.multi
    def add_history_lines(self):
        """
        Creating saleorder line with purchase history lines
        """
        self.ensure_one()
        active_id = self._context.get('active_id')
        order_id = self.env['sale.order'].browse(active_id)
        line_ids = self.purchase_history_ids
        for line_id in line_ids:
            if line_id.qty_to_be != 0.0:
                sale_order_line = {'product_id' : line_id.order_line.product_id.id,
                                   'product_uom' : line_id.order_line.product_uom.id,
                                   'product_uom_qty' : line_id.qty_to_be,
                                   'price_unit' : line_id.order_line.price_unit,
                                   'order_id' : order_id and order_id.id or False,
                                   'lst_price':line_id.order_line.product_id.lst_price,
                                   'price_from':line_id.order_line.price_from and line_id.order_line.price_from.id
                                   # 'working_cost':line_id.order_line.product_id.cost,
                }
                self.env['sale.order.line'].create(sale_order_line)
        return True


AddPurchaseHistorySO()
