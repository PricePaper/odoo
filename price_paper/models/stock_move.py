# -*- coding: utf-8 -*-

from odoo import fields, models, api


class StockMove(models.Model):
    _inherit = 'stock.move'

    picking_partner_id = fields.Many2one('res.partner', related='picking_id.partner_id', string='Partner')


StockMove()

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    picking_partner_id = fields.Many2one('res.partner', related='move_id.picking_partner_id', string='Partner')


StockMoveLine()
