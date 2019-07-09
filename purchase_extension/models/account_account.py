# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from dateutil.relativedelta import relativedelta
from datetime import datetime


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    discount_due_date = fields.Date(compute='compute_discount_due_date', string='Discount Due Date', store=True)

    @api.depends('payment_term_id.due_days', 'date_invoice')
    def compute_discount_due_date(self):
        for invoice in self:
            invoice.discount_due_date = False
            if invoice.date_invoice and invoice.payment_term_id and invoice.payment_term_id.due_days:
                invoice.discount_due_date = datetime.strptime(invoice.date_invoice, '%Y-%m-%d') + relativedelta(days=invoice.payment_term_id.due_days)

AccountInvoice()




