# -*- coding: utf-8 -*-
from odoo import models, fields, registry, api,_




class TruckRoute(models.Model):

    _name = 'truck.route'

    name = fields.Char(string='Name')
    set_active = fields.Boolean(string='Set Active')


TruckRoute()
