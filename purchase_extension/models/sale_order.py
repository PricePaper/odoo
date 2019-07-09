# -*- coding: utf-8 -*-

from odoo import models, fields, registry, api,_
from datetime import datetime


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    product_arrival_date = fields.Datetime(string='Product Arrival Date', compute='compute_arrival_date')

    @api.depends('product_id')
    def compute_arrival_date(self):
        for line in self:
            if line.product_id:
                query = """
                        SELECT o.release_date from purchase_order o, purchase_order_line
                        l WHERE o.release_date is not null AND o.id=l.order_id AND
                        l.product_id = (%d) AND o.state IN ('purchase', 'done') ORDER BY o.release_date DESC limit 1;""" % (line.product_id.id)
                self.env.cr.execute(query)
                result = self.env.cr.fetchone()
                if result and result[0] > str(datetime.now()):
                    line.product_arrival_date = result[0]


SaleOrderLine()
