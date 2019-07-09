# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
import datetime
from odoo.exceptions import UserError

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    sales_person_ids = fields.Many2many('res.partner', related='partner_id.sales_person_ids', string='Associated Sales Persons')


    @api.multi
    def invoice_validate(self):
        res = super(AccountInvoice, self).invoice_validate()
        for invoice in self:
            rec = invoice.calculate_commission()
        return res

    @api.multi
    def action_invoice_paid(self):
        res = super(AccountInvoice, self).action_invoice_paid()
        for invoice in self:
            rec = invoice.calculate_commission()
            if rec and invoice.state == 'paid':
                rec.write({'is_paid': True})
                invoice.check_due_date(rec)
        return res

    @api.multi
    def action_cancel(self):
        res = super(AccountInvoice, self).action_cancel()
        for invoice in self:
            commission_rec = self.env['sale.commission'].search([('invoice_id', '=', self.id)])
            commission_rec and commission_rec.unlink()
        return res

    def check_due_date(self, lines):


        for line in lines:
            due_date = datetime.datetime.strptime(self.date_due, '%Y-%m-%d').date()
            if datetime.date.today() > due_date:
                extra_days = datetime.date.today() - due_date
                if self.partner_id.company_id.commission_ageing_ids:
                    commission_ageing = self.partner_id.company_id.commission_ageing_ids.filtered(lambda r : r.delay_days <= extra_days.days)
                    commission_ageing = commission_ageing.sorted(key=lambda r: r.delay_days, reverse=True)
                    if commission_ageing and commission_ageing[0].reduce_percentage:
                        commission = commission_ageing[0].reduce_percentage * line.commission / 100
                        vals = {
                                'sale_person_id' : line.sale_person_id.id,
                                'sale_order': line.sale_order,
                                'commission': -commission,
                                'invoice_id' : self.id,
                                'invoice_type' : self.type,
                                'is_paid':True,
                                'invoice_amount':self.amount_total,
                                }
                        commission_rec = self.env['sale.commission'].create(vals)



    def calculate_commission(self):

        if len(self.invoice_line_ids) == 1 and self.invoice_line_ids[0].quantity < 0:
            return False
        commission_rec = self.env['sale.commission'].search([('invoice_id', '=', self.id)])
        if not commission_rec and self.type in ['out_invoice','out_refund']:
            for rec in self.partner_id.commission_percentage_ids:
                if not rec.rule_id:
                    raise UserError(_('Commission rule is not configured for %s.' %(rec.sale_person_id.name)))
                commission = 0
                if rec.rule_id.based_on in ['profit', 'profit_delivery']:
                    commission = self.gross_profit  * (rec.rule_id.percentage/100)
                elif rec.rule_id.based_on =='invoice':
                    commission = self.amount_total * (rec.rule_id.percentage/100)
                if self.type == 'out_refund':
                    commission = -commission
                vals = {
                        'sale_person_id' : rec.sale_person_id.id,
                        'sale_order': self.origin,
                        'commission': commission,
                        'invoice_id' : self.id,
                        'invoice_type' : self.type,
                        'is_paid':False,
                        'invoice_amount':self.amount_total,
                        }
                commission_rec = self.env['sale.commission'].create(vals)
        return commission_rec



AccountInvoice()
