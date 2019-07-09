# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
import datetime
from datetime import timedelta, date
from odoo.exceptions import ValidationError

class AccountPaymentTermLine(models.Model):
    _inherit = "account.payment.term.line"

    grace_period = fields.Integer(help="Gives the number of days extended for the customer after defaulting payments.", string='Customer Grace Period')


AccountPaymentTermLine()


class AccountFiscalPosition(models.Model):
    _inherit = "account.fiscal.position"

    code = fields.Char(string='Code')


AccountFiscalPosition()


class AccountMove(models.Model):
    _inherit = "account.move.line"

    date_maturity_grace = fields.Date(string='Grace period Date')


AccountMove()


class AccountInvoice(models.Model):
    _inherit = "account.invoice"


    gross_profit = fields.Monetary(compute='calculate_gross_profit', string='Gross Profit')


    @api.multi
    def invoice_validate(self):

        for invoice in self:
            if not invoice.payment_term_id and invoice.type in ('out_invoice', 'in_invoice'):
                raise ValidationError(_('Payment term is not set for invoice %s' % (invoice.number)))
        res = super(AccountInvoice, self).invoice_validate()
        return res


    @api.multi
    def action_invoice_cancel(self):
        if self.state == 'draft':
            return super(AccountInvoice, self).action_invoice_cancel()
        if not self.env.user.has_group('account.group_account_manager'):
            raise ValidationError(_('You dont have permissions to cancel an invoice.'))
        return super(AccountInvoice, self).action_invoice_cancel()



    @api.depends('invoice_line_ids.profit_margin')
    def calculate_gross_profit(self):
        """
        Compute the gross profit in invoice.
        """
        for invoice in self:
            gross_profit = 0
            for line in invoice.invoice_line_ids:
                gross_profit += line.profit_margin
            invoice.update({'gross_profit' : round(gross_profit,2)})



#    @api.multi
#    def action_invoice_open(self):
#        """
#        overriden to raise validation error when unit_price is less than cost price.
#        """

#        for invoice in self:
#            if invoice.type == 'out_invoice':
#                for invoice_line in invoice.invoice_line_ids:
#                    if invoice_line.profit_margin < 0:
#                        msg = '[%s]%s ' % (invoice_line.product_id.default_code,invoice_line.product_id.name) + "Unit Price is less than Product Cost Price"
#                        raise ValidationError(_('%s' % (msg)))
#        res = super(AccountInvoice, self).action_invoice_open()
#        return res


    @api.multi
    def finalize_invoice_move_lines(self, move_lines):
        """
        overriden to set extended the grace period for customer.
        """
        res = super(AccountInvoice, self).finalize_invoice_move_lines(move_lines)


        credit_lines = []
        debit_lines = []
        payment_term = self.payment_term_id

        if payment_term and isinstance(res, list):
            for line in res:
                vals = line[2]

                #Seperate credit and debit lines. We only need to process debit lines.
                if vals.get('credit', False):
                    credit_lines.append(vals)
                if vals.get('debit', False):
                    debit_lines.append(vals)

            for line, term in zip(debit_lines, payment_term.line_ids):
                if line.get('date_maturity'):
                    grace_period_due = str(datetime.datetime.strptime(line.get('date_maturity', ''), "%Y-%m-%d").date() + timedelta(days=term.grace_period))
                    line.update({'date_maturity_grace': grace_period_due})


            #Recreate the original list and return
            res = [(0, 0, line) for line in credit_lines] + [(0, 0, line) for line in debit_lines]
        return res


AccountInvoice()


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"


    profit_margin = fields.Monetary(compute='calculate_profit_margin', string="Profit Margin")
    # color = fields.Text(compute='calculate_profit_margin', string="Color", store=False)



    @api.onchange('product_id')
    def _onchange_product_id(self):
        domain = {}
        self.uom_id = self.product_id.uom_id
        res = super(AccountInvoiceLine, self)._onchange_product_id()
        domain = res.get('domain', {})
        product_uom_domain = domain.get('uom_id', [])
        product_uom_domain.append(('id', 'in', self.product_id.sale_uoms.ids))
        return res



    @api.depends('product_id', 'price_unit', 'quantity')
    def calculate_profit_margin(self):
        """
        Calculate profit margin in account invoice
        """
        for line in self:
            if line.product_id and line.quantity > 0 and line.uom_id:
                product_price = round(line.product_id.cost * line.product_id.uom_id.factor / line.uom_id.factor, 2)
                line_price = line.price_unit
                if line.product_id.uom_id != line.uom_id:
                    line_price = line.price_unit * (100/(100+ line.product_id.categ_id.repacking_upcharge))
                elif line.product_id.uom_id == line.uom_id and line.quantity % 1 != 0.0:
                    numer = line.price_unit * line.quantity
                    denom = (int(line.quantity / 1.0) + ((line.quantity % 1) * (100 + line.product_id.categ_id.repacking_upcharge) / 100))
                    line_price = round(numer / denom, 2)

                line.profit_margin = (line_price - product_price) * line.quantity
                # if line.profit_margin < 0:
                #     line.color = 'R'
                # elif line.profit_margin > 0:
                #     line.color = 'G'
                # else:
                #     line.color = 'B'

    @api.onchange('uom_id')
    def _onchange_uom_id(self):
        res = super(AccountInvoiceLine, self)._onchange_uom_id()
        if self.product_id:
            self._set_taxes()
        return res





    def _set_taxes(self):
        """
        overriden to update the unit price based on the pricelist and
        tax based on resale number and previous sale.
        """
        res = super(AccountInvoiceLine, self)._set_taxes()
        if self.invoice_id.type == 'out_invoice':
            prices_all = self.env['customer.product.price']
            for rec in self.invoice_id.partner_id.customer_pricelist_ids:
                if not rec.pricelist_id.expiry_date or rec.pricelist_id.expiry_date >= str(date.today()):
                    prices_all |= rec.pricelist_id.customer_product_price_ids
            prices_all = prices_all.filtered(lambda r: r.product_id.id == self.product_id.id and r.product_uom.id == self.uom_id.id and (not r.partner_id or r.partner_id.id == self.invoice_id.partner_id.id))
            product_price = 0.0
            for price_rec in prices_all:
                if not price_rec.partner_id and prices_all.filtered(lambda r: r.partner_id):
                    continue
                product_price = price_rec.price
                break
            if not product_price:
                if self.uom_id and self.product_id:
                    product_price = self.product_id.uom_id._compute_price(self.product_id.list_price, self.uom_id) + self.product_id.price_extra
                if self.product_id.uom_id != self.uom_id:
                    product_price = product_price * ((100+self.product_id.categ_id.repacking_upcharge)/100)
            if self.product_id.uom_id == self.uom_id and self.quantity % 1 != 0.0:
                product_price = ((int(self.quantity / 1) * product_price) + ((self.quantity % 1) * product_price * ((100+self.product_id.categ_id.repacking_upcharge)/100))) / self.quantity
            self.price_unit = product_price

            partner_history = self.env['sale.order.line'].search([('order_id.partner_shipping_id', '=', self.invoice_id.partner_shipping_id and self.invoice_id.partner_shipping_id.id), ('product_id', '=', self.product_id and self.product_id.id), ('is_last', '=', True)])
            if self.invoice_id and self.invoice_id.partner_id.vat and partner_history and not partner_history.tax_id:
                self.invoice_line_tax_ids = [(5, _, _)] # clear all tax values, no Taxes to be used


        return res


AccountInvoiceLine()
