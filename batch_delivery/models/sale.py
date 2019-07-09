# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError



class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'


    lot_id = fields.Many2one('stock.production.lot', 'Lot')


    @api.onchange('product_id')
    def _onchange_product_id_set_lot_domain(self):
        available_lot_ids = []
        if self.order_id.warehouse_id and self.product_id:
            location = self.order_id.warehouse_id.lot_stock_id
            quants = self.env['stock.quant'].read_group([
                ('product_id', '=', self.product_id.id),
                ('location_id', 'child_of', location.id),
                ('quantity', '>', 0),
                ('lot_id', '!=', False),
            ], ['lot_id'], 'lot_id')
            available_lot_ids = [quant['lot_id'][0] for quant in quants]
        self.lot_id = False
        return {
            'domain': {'lot_id': [('id', 'in', available_lot_ids)]}
        }


    @api.onchange('lot_id')
    def _onchange_product_id_lot_qty_warning(self):
        if self.lot_id and self.lot_id.quant_ids:

            quants = self.lot_id.quant_ids.filtered(lambda q: q.location_id.usage in ['internal'])
            product_qty = sum(quants.mapped('quantity'))

            warning_mess = {
                'title': _('Warning!'),
                'message' : _('Please note that there are only %s quantities of %s currently in this lot' %(product_qty, self.product_id.name))
            }
            res = {'warning': warning_mess}
            return res



SaleOrderLine()
