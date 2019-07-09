# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.



from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError



class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"



    advance_payment_method = fields.Selection([
        ('delivered', 'Invoiceable lines'),
        ('all', 'Invoiceable lines (deduct down payments)'),
        ('percentage', 'Down payment (percentage)'),
        ('fixed', 'Down payment (fixed amount)')
        ], string='What do you want to invoice?', default='all', required=True)


#    @api.constrains('advance_payment_method')
#    def check_payment_method(self):
#        for rec in self:
#            if rec.advance_payment_method != 'all':
#                raise ValidationError(_('You can only choose the option invoicable lines(deduct down payments) for this order!'))



SaleAdvancePaymentInv()
