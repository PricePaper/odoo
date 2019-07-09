# -*- coding: utf-8 -*-

from odoo import models, fields, registry, api,_
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    release_date = fields.Datetime(string='Release Date')
    total_volume = fields.Float(string="Total Order Volume", compute='_compute_total_weight_volume')
    total_weight = fields.Float(string="Total Order Weight", compute='_compute_total_weight_volume')


    @api.depends('order_line.product_id', 'order_line.product_qty')
    def _compute_total_weight_volume(self):
        for order in self:
            volume = 0
            weight = 0
            for line in order.order_line:
                volume += line.gross_volume
                weight += line.gross_weight
            order.total_volume = volume
            order.total_weight= weight

    @api.multi
    def add_sale_history_to_po_line(self):
        if not self.partner_id:
            return False
        result_list = []
        all_supplier_info = self.env['product.supplierinfo'].search([('name', '=', self.partner_id.id)])
        all_vendor_products = []
        for rec in all_supplier_info:
            if rec.product_id:
                all_vendor_products.append(rec.product_id.id)
            else:
                prod_ids = rec.product_tmpl_id.product_variant_ids and rec.product_tmpl_id.product_variant_ids.ids or []
                for prod in prod_ids:
                    all_vendor_products.append(prod)

        product_ids = tuple(all_vendor_products) if len(all_vendor_products)>1 else all_vendor_products and all_vendor_products[0] or 0
        operator = 'in' if len(all_vendor_products)>1 else '='
        if all_vendor_products:
            current_date = date.today()
            first_day = current_date.replace(day=1)
            date_limit = str(first_day + relativedelta(months=-15))
            self._cr.execute("SELECT date_trunc('month', so.confirmation_date) AS cnf_date, sol.product_id, sol.product_uom, sum(sol.product_uom_qty) FROM sale_order_line sol JOIN sale_order so on so.id=sol.order_id WHERE so.state in ('sale', 'done') AND sol.product_id %s %s and so.confirmation_date >= '%s' GROUP BY sol.product_id, sol.product_uom, cnf_date ORDER BY sol.product_id, sol.product_uom, cnf_date desc" %(operator, product_ids, str(date_limit) ))

            res = self._cr.dictfetchall()
            if not res:
                raise ValidationError(_('No history of products found being sold in the last 15 months.'))
            result_dict = {}
            product_id = False
            for element in res:
                if product_id != element['product_id']:
                    product_id = element['product_id']
                    result_dict.update({product_id:[{
                                                    'period': element['cnf_date'],
                                                    'units': element['sum'],
                                                    'uom': element['product_uom'],
                                                    }]})
                else:
                    result_dict[product_id].append({'period': element['cnf_date'],
                                                    'units': element['sum'],
                                                    'uom': element['product_uom'],
                                                     })
            result_list = self.sanitize_uom(result_dict)

        context ={'data' : result_list}
        view_id = self.env.ref('purchase_extension.view_sale_history_add_po_wiz').id
        return {
            'name': _('Add sale history to PO'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'add.sale.history.po',
            'view_id': view_id,
            'type': 'ir.actions.act_window',
            'context' : context,
            'target' :'new'
        }



    @api.model
    def sanitize_uom(self, result_dict):
        """
        processes the query result into a standard dictionary
        vals parameter for create argument of Odoo
        """
        # Converts the result_dict quantities to purchase unit scale
        for ele in result_dict.keys():
            product_purchase_unit = self.env['product.product'].browse(ele).uom_po_id
            for row in result_dict[ele]:
                if row['uom'] != product_purchase_unit.id:
                    changed_uom_qty = self.env['product.uom'].browse(row['uom'])._compute_quantity(row['units'], product_purchase_unit)
                    row['uom'] = product_purchase_unit.id
                    row['units'] = changed_uom_qty

        # merges values of same period to a single record
        result_dict2 = {}
        for ele in result_dict.keys():
            result_dict2.update({ele:{}})
            for row in result_dict[ele]:
                if not result_dict2[ele].get(row['period'], False):
                    result_dict2[ele].update({row['period']:row['units']})
                else:
                    current_count = result_dict2[ele].get(row['period'])
                    result_dict2[ele].update({row['period']:row['units'] + current_count})



        # Formats the result to a key value pair where key is the product id and values is a dictionary with key as period and value as quantity
        current_date = date.today()
        first_day = current_date.replace(day=1)
        first_month_list = [str((first_day + relativedelta(months=-x)).strftime('%Y-%m-%d %H:%M:%S')) for x in range (0, 15)]
        date_matrix = {ele: 'month'+str(x) for x, ele in zip(range(1, 16), first_month_list)}
        for key in result_dict2.keys():
            result = {}
            for ele in date_matrix.keys():
                if ele in result_dict2[key].keys():
                    result.update({date_matrix[ele]: result_dict2[key][ele]})
                else:
                    result.update({date_matrix[ele]:0})
            result_dict2[key] = result



        # Converts the result into list of standard dictionarys vals parameter for create argument in Odoo
        result_list = []
        for k in result_dict2.keys():
            month_data = result_dict2[k]
            month_data.update({'product_id': k,
                               'product_pseudo_id': k,
                              })
            result_list.append(month_data)


        return result_list






PurchaseOrder()



class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    gross_volume = fields.Float(string="Gross Volume", compute='_compute_gross_weight_volume')
    gross_weight = fields.Float(string="Gross Weight", compute='_compute_gross_weight_volume')



    @api.depends('product_id.volume', 'product_id.weight')
    def _compute_gross_weight_volume(self):
        for line in self:
            volume = line.product_id.volume * line.product_qty
            weight = line.product_id.weight * line.product_qty
            line.gross_volume = volume
            line.gross_weight= weight

    @api.multi
    def show_sales_history(self):
        """
        returns the historical sales of this
        product for the past 15 months
        """
        current_date = date.today()
        first_day = current_date.replace(day=1)
        date_limit = str(first_day + relativedelta(months=-15))
        self._cr.execute("SELECT sol.id FROM sale_order_line sol JOIN sale_order so on so.id=sol.order_id WHERE sol.product_id=%s AND so.confirmation_date>='%s' and so.state in ('sale', 'done')" %(self.product_id.id, date_limit))
        res = self._cr.dictfetchall()
        sale_lines = [ele['id'] for ele in res]
        sale_lines = self.env['sale.order.line'].browse(sale_lines)
#        sale_lines = self.env['sale.order.line'].search([('product_id', '=', self.product_id.id), ('order_id.confirmation_date', '>=', date_limit), ('order_id.state', 'in', ('sale', 'done'))])
        if not sale_lines:
            raise ValidationError(_('No history of product found being sold in the last 15 months.'))
        created_ids = []
        for ele in sale_lines:
            uom_qty = ele.product_uom_qty
            #change uom to purchase units
            if ele.product_uom.id != ele.product_id.uom_po_id.id:
                uom_qty = ele.product_uom._compute_quantity(uom_qty, ele.product_id.uom_po_id)
            created_ids += self.env['view.sales.history.po'].create({'product_id': ele.product_id.id,
                                                                     'date': ele.order_id.confirmation_date,
                                                                     'quantity': uom_qty,
                                                                     'uom': ele.product_id.uom_po_id.id,
                                                                     'partner_id': ele.order_id.partner_id.id,
                                                                     'sale_line_id': ele.id,
                                                                    })
        action = self.env.ref('purchase_extension.action_view_sales_history_po').read()[0]
        action['domain'] = [("id", "in", [r.id for r in created_ids])]
        action['target'] = 'new'
        return action

PurchaseOrderLine()

