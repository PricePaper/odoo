# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ProcurementRule(models.Model):
    _inherit = "procurement.rule"

    # @api.model
    # def _run_move_create(self, procurement):
    #     res = super(ProcurementOrder, self)._run_move_create(procurement)
    #     location_id = procurement.line_id.product_id.property_stock_location.id or \
    #         procurement.line_id.product_id.categ_id.property_stock_location.id or \
    #         procurement.line_id.order_id.warehouse_id.lot_stock_id.id
    #     if location_id:
    #         res.update({'location_id':location_id})
    #     return res

    def _get_stock_move_values(self, product_id, product_qty, product_uom, location_id, name, origin, values, group_id):
        res = super(ProcurementRule, self)._get_stock_move_values(product_id, product_qty, product_uom, location_id, name, origin, values, group_id)
        location_src = product_id and product_id.property_stock_location and \
                product_id.property_stock_location.id or product_id and \
                product_id.categ_id and product_id.categ_id.property_stock_location and \
                product_id.categ_id.property_stock_location.id or False
        if location_src:
            res.update({'location_id': location_src})
        return res

ProcurementRule()
