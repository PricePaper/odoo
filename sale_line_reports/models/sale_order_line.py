# -*- coding: utf-8 -*-

from odoo import models, fields, registry, api,_


class SaleOrderline(models.Model):
    _inherit = 'sale.order.line'

    customer_code = fields.Char(related='order_id.partner_id.customer_code', string='Cust.#')
    date_order = fields.Datetime(related='order_id.date_order', string='Order Date')
    customer_po = fields.Char(related='order_id.client_order_ref', string='Cust P/O#')
    is_taxed = fields.Char(string='TX', compute='_is_taxed')
    cost = fields.Float(string='Cost', related='product_id.cost')
    percent = fields.Float(string='PCT', compute='_calculate_percent')
    lst_price = fields.Float(string='STD Price', related='product_id.lst_price')
    class_margin = fields.Float(related='product_id.categ_id.class_margin')
    company_margin = fields.Float(related='company_id.company_margin')
    remark = fields.Char(string='RM', compute='_calculate_remark')


    @api.multi
    def _calculate_percent(self):
        for line in self:
            if line.cost:
                line.percent = ((line.price_unit - line.cost)/line.cost) * 100


    @api.multi
    def _is_taxed(self):
        for line in self:
            if line.tax_id:
                line.is_taxed = 'T'
            else:
                line.is_taxed = ''


    @api.multi
    def _calculate_remark(self):
        for line in self:
            remarks = []
            rem = ''

            if line.percent < line.company_margin:
                remarks.append('BM')
            elif line.percent > line.company_margin:
                remarks.append('AM')

            if line.percent < line.class_margin:
                remarks.append('CBM')
            elif line.percent > line.class_margin:
                remarks.append('CAM')

            if not line.price_unit:
                remarks.append('NC')

            if line.product_id.standard_price == line.price_unit:
                remarks.append('FC')

            if line.product_id.cost == line.price_unit:
                remarks.append('C')
            elif line.product_id.cost > line.price_unit:
                remarks.append('BC')

            if line.new_product:
                remarks.append('NP')
            if line.manual_price:
                remarks.append('M')

            if remarks:
                remarks = str(remarks).replace("'", '').replace("[", '').replace("]", '')

            line.remark = remarks


SaleOrderline()
