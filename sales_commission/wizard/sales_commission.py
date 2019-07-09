# -*- coding: utf-8 -*-


from odoo import models, fields, api
#from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import  datetime, date
from dateutil.relativedelta import relativedelta
import calendar


class SalesCommission(models.TransientModel):
    _name = 'sales.commission'
    _description = 'Show Sales commission'

    confirmation_date = fields.Date(string='Date')
    sales_person = fields.Many2one('res.partner', string='Sales Person')
    # order = fields.Many2one('sale.order', string='Sale order')
    sale_order = fields.Char(string='Sale Order')
    order_total = fields.Float(string='Sale order Total')
    invoice_paid = fields.Float(string='Invoice Paid')
    commission = fields.Float(string='Commission Earned')
    user_id = fields.Integer(string='User')
    commission_based_on = fields.Char(string='Commission Based on')
    commission_percentage = fields.Float(string='Commission Percentage')
    profit = fields.Float(string='Profit Generated')
    max_draw = fields.Float(string='Max Draw Amount This Month (Calculated)')
    draw_till_date = fields.Float(string='Draw Amount Till Date (Calculated)')

SalesCommission()

class SalesUnpaidCommission(models.TransientModel):
    _name = 'sales.unpaid.commission'
    _description = 'Show Sales commission'

    confirmation_date = fields.Date(string='Date')
    sales_person = fields.Many2one('res.partner', string='Sales Person')
    # order = fields.Many2one('sale.order', string='Sale order')
    sale_order = fields.Char(string='Sale Order')
    order_total = fields.Float(string='Sale order Total')
    invoice_paid = fields.Float(string='Invoice Paid')
    commission = fields.Float(string='Commission')
    user_id = fields.Integer(string='User')
    commission_based_on = fields.Char(string='Commission Based on')
    commission_percentage = fields.Float(string='Commission Percentage')
    profit = fields.Float(string='Profit')
    max_draw = fields.Float(string='Max Draw Amount This Month (Calculated)')
    draw_till_date = fields.Float(string='Draw Amount Till Date (Calculated)')

SalesUnpaidCommission()

class GenerateCommission(models.TransientModel):
    _name = 'generate.sales.commission'
    _description = 'Generate Sales commission'


    @api.model
    def _get_months(self):
        res = []
        startdate = datetime.now()
        for i in range(0,12):
            date = startdate - relativedelta(months=i)
            key = format(date, '%m-%Y')
            value = format(date, '%B %Y')
            res.append((key, value))
        return res

    month = fields.Selection(string="Month", selection=_get_months, required=True)
    report_type = fields.Selection([('invoice_paid', 'Invoice Paid Orders'), ('payment_pending', 'Payment Pending Orders')], string='Calculated For', default='invoice_paid', required=True)
    salesperson_id = fields.Many2one('res.partner', string='Sales Persons', domain=[('is_sales_person', '=', True)])


    @api.multi
    def generate_commission(self):
        self.ensure_one()
        if self.report_type == 'invoice_paid':
            return self.generate_commission_invoice_paid()
        else:
            return self.generate_commission_payment_pending()


    @api.model
    def generate_commission_invoice_paid(self):
        """
        method for calculate generated commission
        """
        self.env['sales.commission'].sudo().search([('user_id', '=', self.env.user.partner_id.id)]).unlink()
        self.calculate_commission()
        pivot_id = self.env.ref('sales_commission.view_order_sales_commission_pivot').id
        res = {
            "type": "ir.actions.act_window",
            "name" : "Sale commission",
            "res_model": "sales.commission",
            "views": [[pivot_id, "pivot"]],
            "context": {'group_by':['sales_person']},
            "domain": [["user_id", "=", self.env.user.partner_id.id]],
            "target": "current",
        }
        return res

    @api.model
    def generate_commission_payment_pending(self):
        """
        method for calculate pending commission
        """
        self.env['sales.unpaid.commission'].sudo().search([('user_id', '=', self.env.user.partner_id.id)]).unlink()
        self.calculate_commission()
        pivot_id = self.env.ref('sales_commission.view_order_sales_commission_pending_pivot').id
        res = {
            "type": "ir.actions.act_window",
            "name" : "Sale Unpaid Commission",
            "res_model": "sales.unpaid.commission",
            "views": [[pivot_id, "pivot"]],
            "context": {'group_by':['sales_person']},
            "domain": [["user_id", "=", self.env.user.partner_id.id]],
            "target": "current",
        }
        return res


    def calculate_commission(self):
        """
        common method for calculate commission
        """
        month = self.month.split('-')[0]
        year = self.month.split('-')[1]
        month_last_date = calendar.monthrange(int(year), int(month))[1]
        from_date = "%s-%s-01 00:00:00" %(year, month)
        to_date = "%s-%s-%s 00:00:00" %(year, month, month_last_date)

        salespersons = []

        commission_entries = self.env['sale.commission'].search([('write_date', '>=', from_date), ('write_date', '<=', to_date)])
        commissions = self.env['sale.commission']
        if self.env.user.has_group('sales_commission.group_sales_commission'):
            commissions = commission_entries
            if self.salesperson_id:
                commissions = commission_entries.filtered(lambda r: r.sale_person_id == self.salesperson_id)

        elif self.env.user.has_group('sales_team.group_sale_salesman'):
            commissions = commission_entries.filtered(lambda r: r.sale_person_id == self.env.user.partner_id)
        for commission_line in commissions:
        # for commission_line in commission_entries:
                if commission_line.sale_person_id not in salespersons:
                    salespersons.append(commission_line.sale_person_id)
                commission_dict = {'sales_person' : commission_line.sale_person_id.id,
                                   'confirmation_date': commission_line.write_date,
                                   'sale_order': commission_line.sale_order,
                                #    'order_total': order.amount_total,
                                   'invoice_paid': commission_line.invoice_amount,
                                   'commission': commission_line.commission,
                                #    'commission_based_on' : 'Based on ' + dict(rec.rule_id._fields['based_on'].selection).get(rec.rule_id.based_on),
                                #    'commission_percentage' : rec.rule_id.percentage,
                                   'user_id': self.env.user.partner_id.id,
                                   'profit': commission_line.invoice_id.gross_profit,
                                   }

                if commission_line.is_paid:
                    self.env['sales.commission'].create(commission_dict)
                else:
                    self.env['sales.unpaid.commission'].create(commission_dict)
        for salesperson in salespersons:
            draw_till_today, max_draw_this_month = self.get_draw_amount_this_month(int(month), int(year), month_last_date, salesperson)
            vals = {
                    'sales_person' : salesperson.id,
                    'user_id': self.env.user.partner_id.id,
                    'max_draw': max_draw_this_month,
                    'draw_till_date': draw_till_today,
                    }
            self.env['sales.commission'].create(vals)
            self.env['sales.unpaid.commission'].create(vals)





    @api.model
    def get_draw_amount_this_month(self, month, year, month_last_date, sale_person):

        daily_draw = sale_person.weekly_draw/5
        weekday_count = 0
        weekdays_till_this_month = 0
        month_begin_date = date(year, month, 1)
        month_end_date = date(year, month, month_last_date)
        Flag = False
        while(month_begin_date <= month_end_date):

            if month_begin_date.weekday() not in (5,6):
                weekday_count+=1
                if date.today() >= month_begin_date:
                    weekdays_till_this_month+=1
            month_begin_date = month_begin_date + relativedelta(days=1)

        draw_till_today = daily_draw * weekdays_till_this_month
        max_draw_this_month = daily_draw * weekday_count
        return draw_till_today, max_draw_this_month

GenerateCommission()
