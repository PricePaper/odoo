# -*- coding: utf-8 -*-

from odoo import models, fields, registry, api,_


class CommissionPercentage(models.Model):
    _name = 'commission.percentage'

    sale_person_id = fields.Many2one('res.partner', string='Sales Person')
    partner_id = fields.Many2one('res.partner', string='Customer')
    rule_id = fields.Many2one('commission.rules', string='Rule')

    @api.onchange('sale_person_id')
    def sale_person_id_change(self):
        if self.sale_person_id:
            self.rule_id = self.sale_person_id.default_commission_rule

CommissionPercentage()
