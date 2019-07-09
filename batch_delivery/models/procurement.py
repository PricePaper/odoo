# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class ProcurementRule(models.Model):

    _inherit = 'procurement.rule'


    def _get_stock_move_values(self, product_id, product_qty, product_uom, location_id, name, origin, values, group_id):
        res = super(ProcurementRule, self)._get_stock_move_values(product_id, product_qty, product_uom, location_id, name, origin, values, group_id)
        transit_location = self.env['stock.location'].search([('is_transit_location', '=', True)], limit=1)
        if transit_location:
            res.update({'location_dest_id': transit_location.id})
        else:
            raise UserError(_("Please go to stock locations and select a stock transit location by checking the field with string Truck Transit Location."))
        return res

ProcurementRule()
