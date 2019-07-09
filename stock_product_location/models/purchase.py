# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

#    @api.multi
#    def _get_destination_location(self):
#        return self.product_id.property_stock_location.id or self.product_id.categ_id.property_stock_location.id or self.order_id.picking_type_id.default_location_dest_id.id or False                





    @api.multi
    def _prepare_stock_moves(self, picking):
        """ overriden to update the line by line destination_location
            for every stock move when received
        """
        res = super(PurchaseOrderLine, self)._prepare_stock_moves(picking)
        product_loc_id = self.product_id.property_stock_location.id or self.product_id.categ_id.property_stock_location.id or False
        if product_loc_id:
            res[0].update({'location_dest_id': product_loc_id})

        return res





PurchaseOrderLine()
