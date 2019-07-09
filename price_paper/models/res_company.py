# -*- coding: utf-8 -*-

from odoo import fields, models, api

class ResCompany(models.Model):
    _inherit = 'res.company'


    burden_percent = fields.Float(string='Burden %')
    partner_delivery_method_id = fields.Many2one('delivery.carrier', string='Delivery Method')
    partner_country_id = fields.Many2one('res.country', string='Country')
    partner_state_id = fields.Many2one('res.country.state', string='State')


ResCompany()
