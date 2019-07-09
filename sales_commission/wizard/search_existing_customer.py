# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from datetime import datetime

class SearchExistingCustomer(models.TransientModel):

    _name = "search.existing.customer"

    search_string = fields.Char(string='Customer Name')
    line_ids = fields.One2many('existing.customer.line', 'parent_id', string='Result')


    @api.onchange('search_string')
    def search_existing_customer(self):
        self.line_ids = []
        if self.search_string != False:
            string = '%'+self.search_string+'%'
            query = """SELECT name, commercial_company_name, email, phone, mobile, vat, last_so, last_so_date from res_partner where (name ilike('%s') or phone ilike('%s') or mobile ilike('%s') or email ilike('%s') or commercial_company_name ilike('%s') or vat ilike('%s')) and customer=True;""" % (string, string, string, string, string, string)
            self.env.cr.execute(query)
            result = self.env.cr.fetchall()
            if result:
                res = []
                for rec in result:
                    val = {'name': rec[0],
                           'email': rec[2],
                           'phone': rec[3],
                           'mobile': rec[4],
                           'tin': rec[5],
                           'last_so': rec[6],
                           'last_so_date': rec[7],
                           'parent_id': self.id,
                           }
                    res.append((0, _, val))
                self.line_ids = res
            else:
                pass




SearchExistingCustomer()


class ExistingCustomerLine(models.TransientModel):

    _name = "existing.customer.line"

    name = fields.Char(string='Customer Name')
    email = fields.Char(string='Email')
    phone = fields.Char(string='Phone')
    mobile = fields.Char(string='Mobile')
    tin = fields.Char(string='Tin')
    last_so = fields.Char(string='Last Sale order')
    last_so_date = fields.Datetime(string='Last Sale Date')
    parent_id = fields.Many2one('search.existing.customer', string='Parent')

ExistingCustomerLine()
