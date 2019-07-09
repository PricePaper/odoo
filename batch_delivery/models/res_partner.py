# -*- coding: utf-8 -*-

from odoo import models, fields, registry, api,_
from odoo.exceptions import UserError
import werkzeug

def urlplus(url, params):
    return werkzeug.Href(url)(params or None)

class ResPartner(models.Model):
    _inherit = 'res.partner'


    is_driver = fields.Boolean(string='Truck Driver')
    delivery_notes = fields.Char(string='Delivery Notes')
    bill_with_goods = fields.Boolean(string='Bill With Goods', default=True)
    location_url = fields.Char(compute='compute_location_url', string="Location URL")



    @api.depends('partner_latitude','partner_longitude')
    def compute_location_url(self):
        """
        Compute the location url from partner lattitude and longitude
        """
        for rec in self:
            if rec.partner_latitude and rec.partner_longitude:
                params={'partner_ids':rec.id,
                        'partner_url' : rec.customer and 'customers' or 'partners'
                        }
                rec.location_url = urlplus('/google_map', params)



    @api.multi
    def view_partner_location(self):
        """
        Method to view the location in google map.
        """
        if not self.location_url:
            raise UserError(_("Map not available, check lattitude and longitude"))
        return {
              'name'     : 'Partner Location',
              'res_model': 'ir.actions.act_url',
              'type'     : 'ir.actions.act_url',
              'target'   : 'new',
              'url'      :  self.location_url or ""
           }

ResPartner()
