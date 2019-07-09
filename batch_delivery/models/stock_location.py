# -*- coding: utf-8 -*-

from odoo import models, fields






class StockLocation(models.Model):

    _inherit = 'stock.location'


    is_transit_location = fields.Boolean(string='Truck Transit Location')



StockLocation()




