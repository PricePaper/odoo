# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
import calendar
from odoo.exceptions import ValidationError

class ResPartner(models.Model):
    _inherit = 'res.partner'


    destination_code = fields.Char(string='Destination Code')
    corp_name = fields.Char(string='Corporate name ')
    customer_pricelist_ids = fields.One2many('customer.pricelist', 'partner_id', string="Customer Pricelists")
    customer_code = fields.Char(string='Partner Code')
    delivery_day_mon = fields.Boolean(string='Monday')
    delivery_day_tue = fields.Boolean(string='Tuesday')
    delivery_day_wed = fields.Boolean(string='Wednesday')
    delivery_day_thu = fields.Boolean(string='Thursday')
    delivery_day_fri = fields.Boolean(string='Friday')
    delivery_day_sat = fields.Boolean(string='Saturday')
    delivery_day_sun = fields.Boolean(string='Sunday')
    shipping_easiness = fields.Selection([('easy', 'Easy'), ('neutral', 'Neutral'), ('hard', 'Hard')], string='Easiness of shipping')

    @api.model
    def default_get(self, fields_list):
        res = super(ResPartner, self).default_get(fields_list)
        if self.env.user.company_id:
            company = self.env.user.company_id
            res.update({'property_delivery_carrier_id':company.partner_delivery_method_id and company.partner_delivery_method_id.id or False,
            'country_id':company.partner_country_id and company.partner_country_id.id or False,
            'state_id':company.partner_state_id and company.partner_state_id.id or False})
        return res


    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """
        overriden to display the search result
        based on customer code as well
        """
        res = super(ResPartner, self).name_search(name=name, args=args, operator=operator, limit=limit)
        if name:
            domain = [('customer_code', 'ilike', name)]
            if self._context.get('search_default_supplier', False):
                domain.append(('supplier', '=', True))
            elif self._context.get('search_default_customer', False):
                domain.append(('customer', '=', True))
            customer_code_results = self.search(domain)
            customer_code_results = customer_code_results.name_get()
            res = res + customer_code_results
        return res

    @api.constrains('customer_code')
    def check_partner_code(self):
        if self.search([('customer_code', '=ilike', self.customer_code), ('id', '!=', self.id)]):
            raise ValidationError(_('Partner with same Partner code already exists.'))

    @api.model
    def create(self, vals):

        if not vals.get('customer_code', False):
            if 'company_id' in vals:
                while True:
                    customer_code = vals.get('name')[0:3].upper() +  self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code('res.partner')
                    if not self.search([('customer_code', '=ilike', customer_code)]):
                        vals['customer_code'] = customer_code
                        break

            else:
                while True:
                    customer_code = vals.get('name')[0:3].upper() +  self.env['ir.sequence'].next_by_code('res.partner')
                    if not self.search([('customer_code', '=ilike', customer_code)]):
                        vals['customer_code'] = customer_code
                        break

        result = super(ResPartner, self).create(vals)
        if result.customer:
            result.setup_pricelist_for_new_customer()
        return result


    @api.model
    def setup_pricelist_for_new_customer(self):
        pricelist = self.env['product.pricelist'].create({'partner_id': self.id,
                                                          'name': self.customer_code,
                                                          'type': 'customer'})
        self.env['customer.pricelist'].create({'pricelist_id':pricelist.id,
                                               'sequence':1,
                                               'partner_id': self.id})
        return True


ResPartner()

class ResPartnerCategory(models.Model):
    _inherit = 'res.partner.category'

    code = fields.Char(string='Code')


ResPartnerCategory()
