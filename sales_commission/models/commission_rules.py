# -*- coding: utf-8 -*-

from odoo import models, fields, registry, api,_


class CommissionRules(models.Model):
    _name = 'commission.rules'

    sales_person_id = fields.Many2one('res.partner', string='Sales Persons')
    based_on = fields.Selection(selection=[('profit', 'Profit'), ('invoice', 'Paid Invoice'), ('profit_delivery', 'Profit After Delivery')], string='Based on')
    percentage = fields.Float(string='Percentage')


    @api.multi
    @api.depends('based_on', 'percentage')
    def name_get(self):
        result = []
        for record in self:
            name = "%s_%s" % (record.based_on and record.based_on or '', record.percentage and record.percentage or '')
            result.append((record.id,name))
        return result

CommissionRules()
