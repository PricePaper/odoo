# -*- coding: utf-8 -*-

from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

class AddSaleHistoryPoLine(models.TransientModel):

    _name = 'add.sale.history.po.line'

    new_qty = fields.Float(string='New Qty')
    parent_id = fields.Many2one('add.sale.history.po', string="Parent Record")
    product_id = fields.Many2one('product.product', string='Product')
    product_pseudo_id = fields.Many2one('product.product', string='Product')
    product_uom = fields.Many2one('product.uom', related='product_id.uom_po_id', string="UOM")
    product_oh_qty = fields.Float(compute='_calc_qty_available', string='OH Qty')
    product_price = fields.Float(compute='_compute_product_price', string='Price')
    is_not_lowest_price = fields.Boolean(compute ='_check_is_not_low_price', string='Is not Low Price')
    op_max = fields.Float(string='Orderpoint Max', help='Order Point Maximum Quantity', compute="_compute_op_min_max_days")
    op_min = fields.Float(string='Orderpoint Min', help='Order Point Minimum Quantity', compute="_compute_op_min_max_days")
    forecast_days_min = fields.Float(string='Forecast Days Min', help="Forecast days minimum", compute="_compute_op_min_max_days")
    forecast_days_max = fields.Float(string='Forecast Days Max', help="Forecast days maximum", compute="_compute_op_min_max_days")

    month1 = fields.Float(string='Mnt1')
    month2 = fields.Float(string='Mnt2')
    month3 = fields.Float(string='Mnt3')
    month4 = fields.Float(string='Mnt4')
    month5 = fields.Float(string='Mnt5')
    month6 = fields.Float(string='Mnt6')
    month7 = fields.Float(string='Mnt7')
    month8 = fields.Float(string='Mnt8')
    month9 = fields.Float(string='Mnt9')
    month10 = fields.Float(string='Mnt10')
    month11 = fields.Float(string='Mnt11')
    month12 = fields.Float(string='Mnt12')
    month13 = fields.Float(string='Mnt13')
    month14 = fields.Float(string='Mnt14')
    month15 = fields.Float(string='Mnt15')



    @api.depends('product_id')
    def _compute_op_min_max_days(self):
        """
        compute the min op value, max op value.
        min forecast days, max forecast days
        """
        for line in self:
            if line.product_id:
                line.op_max  = line.product_id.orderpoint_ids and line.product_id.orderpoint_ids[0].product_max_qty or 0
                line.op_min  = line.product_id.orderpoint_ids and line.product_id.orderpoint_ids[0].product_min_qty or 0
                po = self._context.get('active_id', False) and self.env['purchase.order'].browse(self._context.get('active_id', False)) or False
                if po:
                    vendor = po.partner_id
                    seller_rec = self.env['product.supplierinfo'].search([('name', '=', vendor.id), ('product_id', '=', line.product_id.id)], limit=1)

                    delay_days_min = 0
                    if seller_rec:
                        delay_days_min = seller_rec.delay
                    if not delay_days_min:
                        delay_days_min = vendor.delay

                    delay_days_max = delay_days_min + vendor.order_freq
                    line.forecast_days_min = delay_days_min
                    line.forecast_days_max = delay_days_max


    @api.depends('product_id')
    def _check_is_not_low_price(self):
        """
        check if this is the vendor with
        lowest price for this product
        """
        for line in self:
            for seller in line.product_id.seller_ids:
                if seller.price < line.product_price:
                    line.is_not_lowest_price = True
                    break


    @api.depends('product_id')
    def _calc_qty_available(self):
        """
        compute on hand quantity in system to purchase units
        """
        for line in self:
            product_purchase_unit = line.product_id.uom_po_id
            changed_uom_qty = line.product_id.uom_id._compute_quantity(line.product_id.qty_available, product_purchase_unit)
            line.product_oh_qty = changed_uom_qty


    @api.model 
    def fields_get(self, allfields=None, attributes=None):
        """
        Overriden to dynamically change 
        the field names of the month fields
        """
        res = super(AddSaleHistoryPoLine, self).fields_get(allfields, attributes=attributes)
        current_date = date.today() 
        first_day = current_date.replace(day=1)
        first_month_list = [str(first_day + relativedelta(months=-x)) for x in range (0, 15)]
        first_month_list = [datetime.strptime(s, '%Y-%m-%d').strftime('%b%y') for s in first_month_list]
        date_matrix = {'month'+str(x):ele for x, ele in zip(range(1, 16), first_month_list)}

        for k in date_matrix.keys():
            if k in res.keys(): 
                res[k]['string'] = date_matrix[k]

        return res



    @api.depends('product_id')
    def _compute_product_price(self):
        if self._context.get('active_model', False) == 'purchase.order' and self._context.get('active_id', False):
            vendor = self.env['purchase.order'].browse(self._context.get('active_id')).partner_id
            for line in self:
                seller_record = line.product_id.seller_ids.filtered(lambda l: l.name.id == vendor.id)
                line.product_price = seller_record and seller_record[0].price or 0.00


AddSaleHistoryPoLine()


class AddSaleHistoryPO(models.TransientModel):

    _name = 'add.sale.history.po'
    _description = "Add Sale History to PO"

    search_box = fields.Char(string='Search')
    sale_history_ids = fields.One2many('add.sale.history.po.line', 'parent_id', string="Sales History")


    @api.onchange('search_box')
    def search_product(self):

        if self._context.get('data', False):
            data = self._context.get('data', False)
            lines = []
            if self.search_box:
                for line in data:
                    product = line.get('product_id', False) and self.env['product.product'].browse(line.get('product_id'))
                    if self.search_box.lower() in product.display_name.lower():
                        lines.append((0, 0, line))
                self.sale_history_ids = lines

            else:
                for line in data:
                    lines.append((0, 0, line))
                self.sale_history_ids = lines




    @api.multi
    def add_history_lines(self):
        """
        Creating saleorder line with purchase history lines
        """
        self.ensure_one()
        active_id = self._context.get('active_id')
        po_id = self.env['purchase.order'].browse(active_id)
        line_ids = self.sale_history_ids
        for line in line_ids:
            if line.new_qty != 0.0:

                rec_name = line.product_id.name
                if line.product_id.description_purchase:
                    rec_name += '\n' + line.product_id.description_purchase

                line_taxes_id = self.env['account.tax']
                fpos = po_id.fiscal_position_id
                if self.env.uid == SUPERUSER_ID:
                    company_id = self.env.user.company_id.id
                    line_taxes_id = fpos.map_tax(line.product_id.supplier_taxes_id.filtered(lambda r: r.company_id.id == company_id))
                else:
                    line_taxes_id = fpos.map_tax(line.product_id.supplier_taxes_id)

                seller = line.product_id.seller_ids.filtered(lambda l: l.name.id == po_id.partner_id.id)
                date_planned = self.env['purchase.order.line']._get_date_planned(seller).strftime(DEFAULT_SERVER_DATETIME_FORMAT)

                po_line = {'product_id' : line.product_id.id,
                           'product_uom' : line.product_uom.id,
                           'product_qty' : line.new_qty,
                           'price_unit' : line.product_price,
                           'order_id' : po_id and po_id.id or False,
                           'name': rec_name,
                           'taxes_id':[(4, t.id, False) for t in line_taxes_id],
                           'date_planned':date_planned,
                }
                self.env['purchase.order.line'].create(po_line)
        return True


AddSaleHistoryPO()
