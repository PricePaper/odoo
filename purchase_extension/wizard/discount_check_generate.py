# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import UserError


class GenerateDiscountCheck(models.TransientModel):

    _name = 'generate.discount.check'

    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    wizard_invoice_ids = fields.One2many('vendor.bill.lines.wizard', 'generate_check_id', string='Invoices')


    @api.onchange('start_date', 'end_date')
    def get_invoices(self):
        vals={}
        if self.start_date and self.end_date:
            vendor_bills1 = self.env['account.invoice']
            vendor_bills = self.env['account.invoice'].search([('type','=','in_invoice'), ('state', '=', 'open'), ('discount_due_date', '>', self.start_date), ('discount_due_date', '<', self.end_date)])

            vendor_bills1 = self.env['account.invoice'].search([('type','=','in_invoice'), ('state', '=', 'open'), ('date_due', '>', self.start_date), ('date_due', '<', self.end_date), ('discount_due_date', '=', False)])
            vendor_bills |= vendor_bills1
            self.wizard_invoice_ids.unlink()
            lines=[]
            for bill in vendor_bills:
                discount_total_amount = bill.amount_total * (100 - bill.payment_term_id.discount_per) /100
                val={
                        'total_amount': bill.amount_total,
                        'partner_id': bill.partner_id.id,
                        'discount_amount': discount_total_amount,
                        'invoice_id': bill.id,
                        'date_invoice': bill.date_invoice,
                        'date_due': bill.date_due,
                        'discount_due_date': bill.discount_due_date,
                        'discount_amount_pseudo': discount_total_amount,
                        'invoice_id_pseudo': bill.id,
                        'select': True,
                    }
                lines.append(val)

            vals.update({'wizard_invoice_ids': lines})
            return {'value' : vals}


    @api.multi
    def generate_check(self):

        bank_journal = self.env['account.journal'].search([('type', '=', 'bank')], limit=1)
        payment_method = self.env['account.payment.method'].search([('code', '=', 'check_printing'), ('payment_type', '=', 'outbound')], limit=1)
        company_id = self.env['res.users'].browse(self.env.uid).company_id
        purchase_writeoff_account = self.env['res.users'].browse(self.env.uid).company_id.purchase_writeoff_account_id
        if not bank_journal:
            raise UserError(_('Bank journal not defined! \nPlease create a bank journal in the system to process these transactions.'))
        if not purchase_writeoff_account:
                raise UserError(_('Please add a purchase writeoff account in the company form page.'))
        partner_group={}
        for invoice in self.wizard_invoice_ids:
            if not invoice.select:
                continue
            if invoice.invoice_id.partner_id.id in partner_group:
                partner_group[invoice.invoice_id.partner_id.id][0]+=invoice.discount_amount
                partner_group[invoice.invoice_id.partner_id.id][1].append((4, invoice.invoice_id.id, 0))
            else:
                partner_group[invoice.invoice_id.partner_id.id] = [invoice.discount_amount, [(4, invoice.invoice_id.id, 0)]]

        for partner in partner_group:
            payment_vals = {
                             'payment_type': 'outbound',
                             'partner_type': 'supplier',
                             'payment_method_id': payment_method.id,
                             'partner_id': partner,
                             'amount': partner_group[partner][0],
                             'journal_id':bank_journal.id,
                             'payment_difference_handling': 'reconcile',
                             'writeoff_label':'Write-Off',
                             'writeoff_account_id': purchase_writeoff_account.id,
                             'invoice_ids': partner_group[partner][1],
                            }
            payment = self.env['account.payment'].create(payment_vals)
            payment.post()



GenerateDiscountCheck()

class VendorBillLines(models.TransientModel):

    _name = 'vendor.bill.lines.wizard'

    total_amount = fields.Float(string='Total Amount')
    partner_id = fields.Many2one('res.partner', string='Vendor')
    discount_amount = fields.Float('Amount After Discount')
    discount_amount_pseudo = fields.Float('Amount After Discount')
    invoice_id = fields.Many2one('account.invoice', string='Invoice')
    invoice_id_pseudo = fields.Many2one('account.invoice', string='Invoice')
    generate_check_id = fields.Many2one('generate.discount.check', string='Parent')
    date_invoice = fields.Date(string='Bill Date')
    date_due = fields.Date(string='Due Date')
    discount_due_date = fields.Date(string='Discount Due Date')
    select = fields.Boolean(string='Select')

VendorBillLines()
