# -*- coding: utf-8 -*-

from odoo import models, fields, registry, api,_


class ResCompany(models.Model):
    _inherit = 'res.company'


    company_margin = fields.Float(string='Company Margin', help='This field is used to specify the company margin for a products category. It is visible in the sale line reports.')




ResCompany()
