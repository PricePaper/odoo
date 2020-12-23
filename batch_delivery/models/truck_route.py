# -*- coding: utf-8 -*-
from odoo import models, fields, registry, api,_
from odoo.exceptions import UserError




class TruckRoute(models.Model):

    _name = 'truck.route'
    _description = 'Truck Route'
    _order = 'name'

    name = fields.Char(string='Name')
    set_active = fields.Boolean(string='Set Active')

    @api.multi
    def unlink(self):
        if self.set_active:
            raise UserError(_('Route is assigned to a batch. First complete the batch to delete the route.'))
        return super(TruckRoute, self).unlink()


TruckRoute()
