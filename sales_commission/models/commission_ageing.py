# -*- coding: utf-8 -*-

from odoo import fields, models, api

class CommissionAgeing(models.Model):
    _name = 'commission.ageing'

    delay_days = fields.Integer(string='Days +')
    reduce_percentage = fields.Float(string='Reduce commission by %')
    company_id = fields.Many2one('res.company', string='Company')

CommissionAgeing()
