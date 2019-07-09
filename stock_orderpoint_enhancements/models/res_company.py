# -*- coding: utf-8 -*-

from odoo import fields, models, api

class ResCompany(models.Model):
    _inherit = 'res.company'

    delay = fields.Integer(string='Delivery Lead Time', help="Lead time in days between the confirmation of the purchase order and the receipt of the products in your warehouse.")
    buffer_percetage = fields.Float(string='OrderPoint Buffer percentage')


ResCompany()
