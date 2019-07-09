# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
import calendar

class DeviatedCost(models.TransientModel):

    _name = "deviated.cost.sale"
    _description = "Deviated Cost Sale"

    @api.model
    def _get_months(self):
        """
        Get previous 12 months in a specified format
        """
        res = []
        startdate = datetime.now()
        for i in range(0,12):
            date = startdate - relativedelta(months=i)
            string = format(date, '%B %Y')
            val = format(date, '%m %Y')
            res.append((val, string))
        return res


    @api.multi
    def print_report(self):
        for record in self:
            month_no,year = self.month.split(" ")
            date_string = "%s-%d-01" %(year,int(month_no))
            from_date=datetime.strptime(date_string, '%Y-%m-%d')
            to_date = from_date.replace(day=calendar.monthrange(int(year), int(month_no))[1])
            data = {
                    'from_date' : from_date,
                    'to_date': to_date,
                    'vendor_id' : self.partner_id.id
                    }
            return self.env.ref('deviated_cost_sale_report.report_deviated_cost_sale').report_action(self.env['sale.order'], data)

    partner_id = fields.Many2one('res.partner', string="Vendor")
    month = fields.Selection(string="Month",  selection=_get_months)



DeviatedCost()
