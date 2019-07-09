# -*- coding: utf-8 -*-

from odoo import fields, models, api
from datetime import date


class CostChange(models.Model):
    _inherit = 'cost.change'



    @api.model
    def default_get(self, fields_list):
        res = super(CostChange, self).default_get(fields_list)
        if self._context.get('product_id', False):
            res['product_id'] = self._context.get('product_id')
        return res

CostChange()
