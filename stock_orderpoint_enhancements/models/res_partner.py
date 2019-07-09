# -*- coding: utf-8 -*-

from odoo import fields, models, api, _

class ResPartner(models.Model):
    _inherit = 'res.partner'




    delay = fields.Integer(
        string='Delivery Lead Time', required=True, default=lambda s: s.default_delay(),
        help="Lead time in days between the confirmation of the purchase order and the receipt of the products in your warehouse.")
    order_freq = fields.Integer(string='Order Frequency')


    @api.model
    def default_delay(self):
        if self.env.user.company_id and self.env.user.company_id.delay:
            return self.env.user.company_id.delay
        return 0


ResPartner()
