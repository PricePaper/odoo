# -*- coding: utf-8 -*-
from odoo import models, fields, api,_



class StockMoveline(models.Model):

    _inherit = "stock.move.line"


    delivery_move_line_id = fields.Many2one('stock.move.line', string='Delivery Move line For')
    delivery_picking_id = fields.Many2one('stock.picking', string='Delivery for Picking', readonly=True, related='delivery_move_line_id.picking_id')
    pref_lot_id = fields.Many2one('stock.production.lot', string='Preferred Lot')





StockMoveline()
