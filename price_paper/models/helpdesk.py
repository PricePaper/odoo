# -*- coding: utf-8 -*-

from odoo import fields, models, api, _

class HelpDeskTeam(models.Model):
    _inherit = 'helpdesk.team'

    is_sales_team = fields.Boolean(string='Sales Team')

HelpDeskTeam()
