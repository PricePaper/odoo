# -*- coding: utf-8 -*-

from odoo import models, fields, registry, api,_


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_sales_person = fields.Boolean(string='Is sale person')
    commission_percentage_ids = fields.One2many('commission.percentage', 'partner_id', string='Sales Persons Commissions')
    default_commission_rule = fields.Many2one('commission.rules', string='Default Commission Rule')
    sales_person_ids = fields.Many2many('res.partner', 'sale_per_id', 'cust_id', compute='get_sales_persons', string='Sales Persons', store=True, inverse="_inverse_set_salespersons")
    customer_ids = fields.Many2many('res.partner', 'cust_id', 'sale_per_id', string='Customers')
    weekly_draw = fields.Float(string='Weekly Draw Amount')
    last_so = fields.Char(string='Last Sale order', compute='get_last_sale_order', store=True)
    last_so_date = fields.Datetime(string='Last Sale Date', compute='get_last_sale_order', store=True)
    sales_person_code = fields.Char(string='Sale Person Code')

    def _inverse_set_salespersons(self):
        for partner in self:
            all_salespersons = [c.sale_person_id.id for c in partner.commission_percentage_ids]
            all_salespersons_brw = self.browse(all_salespersons)
            to_delete = partner.commission_percentage_ids.filtered(lambda c: c.sale_person_id.id not in partner.sales_person_ids.ids)
            to_create = partner.sales_person_ids.filtered(lambda s: s.id not in all_salespersons)
            write_vals = [(0, False, {'sale_person_id': s.id, 'rule_id':s.default_commission_rule and s.default_commission_rule.id or False}) for s in to_create] + [(2, r.id, False) for r in to_delete]
            partner.commission_percentage_ids  = write_vals


    @api.model
    def default_get(self, fields_list):
        res = super(ResPartner, self).default_get(fields_list)
        if self.env.user.partner_id and self.env.user.partner_id.is_sales_person:
            res.update({'commission_percentage_ids':[(0, False, {'sale_person_id': self.env.user.partner_id.id, 'rule_id':self.env.user.partner_id.default_commission_rule and self.env.user.partner_id.default_commission_rule.id or False})]})
        return res

    @api.depends('sale_order_ids.confirmation_date')
    def get_last_sale_order(self):
        for record in self:
            if record.sale_order_ids:
                order = record.sale_order_ids.search([('partner_id', '=', record.id), ('state', 'in', ['sale', 'done'])], order='confirmation_date desc', limit=1)
                if order:
                    record.last_so = order.name
                    record.last_so_date = order.confirmation_date



    @api.depends('commission_percentage_ids.sale_person_id')
    def get_sales_persons(self):
        for record in self:
            if record.commission_percentage_ids:
                sales_persons = record.commission_percentage_ids.mapped('sale_person_id').ids
                record.sales_person_ids = [(6,0,sales_persons)]

    @api.model
    def create(self, vals):
        if not vals.get('commission_percentage_ids') and self.env.user.has_group('sales_team.group_sale_salesman_all_leads') and not self.env.user.has_group('sales_team.group_sale_manager'):
            vals['commission_percentage_ids'] = [(4,self.env['commission.percentage'].create({
                'sale_person_id': self.env.user.partner_id.id,
                'rule_id': self.env.user.partner_id.default_commission_rule.id
                }).id)]
        return super(ResPartner, self).create(vals)

ResPartner()
