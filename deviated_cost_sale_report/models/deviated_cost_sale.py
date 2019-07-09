# -*- coding: utf-8 -*-

from odoo import api, models, _
from odoo.exceptions import ValidationError

class ReportDeviatedCost(models.AbstractModel):
    _name = 'report.deviated_cost_sale_report.deviated_cost_report'

    def get_sale_order_lines(self,data):
        res = []
        domain = [('state','=','sale'), ('confirmation_date', '>=', data.get('from_date')), ('confirmation_date', '<=', data.get('to_date'))]
        sale_orders = self.env['sale.order'].search(domain)
        order_lines = sale_orders.mapped('order_line').filtered(lambda rec:rec.vendor_id.id and rec.rebate_contract_id.id).sorted(key=lambda l: (l.vendor_id.id,l.rebate_contract_id.id))
        if data.get('vendor_id'):
            order_lines = order_lines.filtered(lambda rec:rec.vendor_id.id == data.get('vendor_id'))
        if not order_lines:
            raise ValidationError(_('No records available'))
        line_dict = {}
        for line in order_lines:
            line_dict = {
                        'so_number' : line.order_id.name,
                        'date' : line.order_id.confirmation_date,
                        'product' : "[%s]%s" % (line.product_id.default_code,line.product_id.name),
                        'qty' : line.product_uom_qty,
                        'unit_cost_purchased' : 'purchase_price' in line and  line.purchase_price,
                        'unit_cost_sold' : line.price_unit,
                        'deviated_cost' : 'purchase_price' in line and (line.product_uom_qty * (line.purchase_price-line.price_unit))
                         }
            con_line = {'contract_id' : line.rebate_contract_id,
                    'lines' : [line_dict]
                    }
            if res and res[-1].get('vendor_id',False) == line.vendor_id.id:
                if res[-1]['order_lines'] and res[-1]['order_lines'][-1].get('contract_id',False) == line.rebate_contract_id:
                    res[-1]['order_lines'][-1].get('lines').append(line_dict)
                else:
                    res[-1]['order_lines'].append(con_line)
            else:
                vals = {
                        'vendor_id': line.vendor_id.id,
                        'vendor_name': line.vendor_id.name,
                        'order_lines': [con_line],
                       }
                res.append(vals)
        return res


    @api.model
    def get_report_values(self, docids, data=None):
        return {
                'doc_model': 'sale.order',
                'docs': self.env['account.invoice'],
                'data': data,
                'orders': self.get_sale_order_lines(data)
                }


ReportDeviatedCost()
