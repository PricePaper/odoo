# -*- coding: utf-8 -*-

from odoo import fields, models, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    deviated_contract_ids = fields.Many2many('deviated.cost.contract', string="Rebate Contracts")

ResPartner()
