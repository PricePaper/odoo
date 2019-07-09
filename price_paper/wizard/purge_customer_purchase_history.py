# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from datetime import datetime

class PurgeHistory(models.TransientModel):

    _name = "purge.customer.purchase.history"
    _description = "Purge Customer Purchase History"

    purge_date = fields.Date(string='Select Date')

    @api.multi
    def purge_history(self):
        """
        Delete the purchase history records.
        """
        for rec in self:
            purge_date = datetime.strptime(rec.purge_date, "%Y-%m-%d").date()
            purge_date = datetime.combine(purge_date, datetime.min.time()).strftime("%Y-%m-%d 00:00:00")
            rec.purge_date and self.env['customer.price.history'].search([('order_date', '<', purge_date)]).unlink()

PurgeHistory()
