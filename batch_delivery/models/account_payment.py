from odoo import models, fields


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    batch_id = fields.Many2one('stock.picking.batch', string='Delivery Batch')


AccountPayment()
