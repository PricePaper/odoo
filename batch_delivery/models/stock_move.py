# -*- coding: utf-8 -*-
from odoo import models, fields, api,_



class StockMove(models.Model):

    _inherit = "stock.move"


    picking_status = fields.Char(string='Picking Status', compute='_compute_picking_state')
    delivery_notes = fields.Char(string='Delivery Notes', related='partner_id.delivery_notes')
    delivery_move_id = fields.Many2one('stock.move', string='Delivery for Move')
    delivery_picking_id = fields.Many2one('stock.picking', string='Delivery for Picking', readonly=True, related='delivery_move_id.picking_id')


    @api.multi
    def _compute_picking_state(self):
        for move in self:
            move.picking_status = move.picking_id and move.picking_id.state or ''



    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        """updates the move line values
           with preferred lot id
        """
        res = super(StockMove, self)._prepare_move_line_vals(quantity=quantity, reserved_quant=reserved_quant)
        if self.sale_line_id and self.sale_line_id.lot_id:
            res.update({'pref_lot_id': self.sale_line_id.lot_id.id})
        return res


    def _update_reserved_quantity(self, need, available_quantity, location_id, lot_id=None, package_id=None, owner_id=None, strict=True):
        """if a lot is preffered then use that lot for reserving the stock move
           also check the quantities currently available for that lot in doing so.
        """
        if self.sale_line_id and self.sale_line_id.lot_id:
            avail_qty = self.sale_line_id.lot_id.product_qty
            if avail_qty > self.sale_line_id.product_uom_qty:
                lot_id = self.sale_line_id.lot_id
        res = super(StockMove, self)._update_reserved_quantity(need, available_quantity, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=strict)
        return res

StockMove()
