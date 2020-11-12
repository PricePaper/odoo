import statistics
from datetime import datetime, date

from dateutil.relativedelta import relativedelta

from odoo import fields, models, api, _
from odoo.addons.queue_job.job import job


class ProductProduct(models.Model):
    _inherit = 'product.product'

    last_purchase_price = fields.Char(string='Last Purchase Price', compute='compute_last_purchase_price', store=False)
    last_po = fields.Many2one('purchase.order', string='Last PO', compute='compute_last_purchase_price', store=False)
    price_margin = fields.Float(string='Margin %', compute='compute_margin')
    competitor_price_ids = fields.One2many('customer.product.price', 'product_id', string='Restuarant depot price',
                                           domain=[('pricelist_id.type', '=', 'competitor')])
    customer_price_ids = fields.One2many('customer.product.price', 'product_id',
                                         domain=[('pricelist_id.type', '=', 'customer')], string='Customer price list')
    median_price = fields.Html(string='Median Prices')
    future_price_ids = fields.One2many('cost.change', 'product_id', string='Future Price',
                                       domain=[('is_done', '=', False), ('product_id', '!=', False)])
    change_flag = fields.Boolean(string='Log an Audit Note')
    audit_notes = fields.Text(string='Audit Note')

    # standard_price_date_lock = fields.Date(string='Standard Price Lock Date')

    #    @api.multi
    #                        @api.onchange('uom_id','standard_price','burden_percent','lst_price','customer_price_ids','competitor_price_ids','future_price_ids')
    #    def onchange_change_flag(self):
    #        action = self.env.ref('price_maintanance.action_price_maintanace')
    #        action = action and action.id
    #        context_action = self._context.get('params', {}).get('action', False)

    #        if context_action == action:
    #            if not self.change_flag:
    #                self.change_flag = True
    #                res =  {'warning': {
    #                                    'title': _('Warning'),
    #                                    'message': _('You have made changes in this form. Please do not forget to enter an audit note under the bottom part of the screen before you save.')
    #                                   }
    #                       }
    #                return res

    @api.multi
    def edit_price(self):
        context = {'product_id': self.id, 'lst_price': self.lst_price, 'cost': self.standard_price,
                   'customer_pricelist': self.customer_price_ids.ids, 'future_price': self.future_price_ids.ids}
        view_id = self.env.ref('price_maintanance.view_price_maintanace_edit').id
        return {
            'name': _('Edit Price'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'price.maintanace.edit',
            'view_id': view_id,
            'type': 'ir.actions.act_window',
            'context': context,
            'target': 'new'
        }

    @api.multi
    def compute_last_purchase_price(self):

        for product in self:
            line = self.env['purchase.order.line'].search(
                [('state', 'in', ('done', 'purchase')), ('product_id', '=', product.id)], order='date_order desc',
                limit=1)
            if line:
                product.last_purchase_price = '%s %s %s' % (line.price_unit, line.product_uom.name, line.date_order)
                product.last_po = line.order_id.id

    @api.depends('lst_price', 'cost')
    def compute_margin(self):
        for product in self:
            if product.cost:
                product.price_margin = 100 * (product.lst_price - product.cost) / product.cost

    def get_median(self, order_lines):

        prices = []
        median = 0
        for line in order_lines:
            product_price = line.product_uom._compute_price(line.price_unit,
                                                            line.product_id.uom_id) + line.product_id.price_extra
            prices.append(product_price)
        if prices:
            median = round(statistics.median(prices), 2)
        return median

    @api.model
    def _calculate_median_price(self):
        today = datetime.now()
        date_10_days_back_start_date = today - relativedelta(days=10)
        date_30_days_back_start_date = today - relativedelta(days=30)
        date_60_days_back_start_date = today - relativedelta(days=60)
        date_90_days_back_start_date = today - relativedelta(days=90)

        unit_price_median_10_day = 100
        orders = self.env['sale.order'].search(
            [('state', 'in', ['sale', 'done']), ('confirmation_date', '>=', str(date_90_days_back_start_date)),
             ('confirmation_date', '<=', str(today))])
        order_lines = self.env['sale.order.line']

        for order in orders:
            order_lines |= order.order_line

        products = self.env['product.product'].search([])
        for product in products:
            sale_order_lines_10_day_back = order_lines.filtered(lambda
                                                                    line: line.product_id.id == product.id and line.order_id.confirmation_date >= date_10_days_back_start_date)
            sale_order_lines_30_day_back = order_lines.filtered(lambda
                                                                    line: line.product_id.id == product.id and line.order_id.confirmation_date >= date_30_days_back_start_date)
            sale_order_lines_60_day_back = order_lines.filtered(lambda
                                                                    line: line.product_id.id == product.id and line.order_id.confirmation_date >= date_60_days_back_start_date)
            sale_order_lines_90_day_back = order_lines.filtered(lambda
                                                                    line: line.product_id.id == product.id and line.order_id.confirmation_date >= date_90_days_back_start_date)
            unit_price_median_10_day = product.get_median(sale_order_lines_10_day_back)
            unit_price_median_30_day = product.get_median(sale_order_lines_30_day_back)
            unit_price_median_60_day = product.get_median(sale_order_lines_60_day_back)
            unit_price_median_90_day = product.get_median(sale_order_lines_90_day_back)

            product.median_price = "<table style='width:500px'>\
            <tr><th>Number of Days</th><th>Median</th></tr>\
            <tr><td>10 Days</td><td>$ {:.02f}</td></tr>\
            <tr><td>30 Days</td><td>$ {:.02f}</td></tr>\
            <tr><td>60 Days</td><td>$ {:.02f}</td></tr>\
            <tr><td>90 Days</td><td>$ {:.02f}</td></tr>\
            </table>".format(unit_price_median_10_day, unit_price_median_30_day, unit_price_median_60_day,
                             unit_price_median_90_day)

    @api.multi
    def write(self, vals):
        change_flag = vals.pop('change_flag', False)
        audit_notes = vals.pop('audit_notes', False)
        res = super(ProductProduct, self).write(vals)
        if change_flag:
            self.create_audit_notes(audit_notes)
        if vals.get('future_price_ids', False):
            self.cost_change_cron_button()
        return res

    @api.multi
    def cost_change_cron_button(self):
        self.env['cost.change'].cost_change_cron()
        return True

    @api.multi
    def create_audit_notes(self, audit_notes):
        for product in self:
            product.env['price.edit.notes'].create({
                'product_id': product.id,
                'edit_date': fields.Datetime.now(),
                'note': audit_notes,
                'user_id': self.env.user.id
            })

    @api.model
    def _cron_update_product_lst_price(self):
        OrderLine = self.env['sale.order.line']
        search_target = self.env.user.company_id.product_lst_price_months or 0
        date_to = datetime.today() - relativedelta(months=search_target, day=1)

        # 6Months products
        domain = [
            ('display_type', '=', False),
            ('order_id.date_order', '>=', date_to.strftime('%Y-%m-%d')),
        ]
        line_data = OrderLine.read_group(domain, ['product_id'], ['product_id'])

        for data in line_data:
            product = self.browse(data['product_id'][0])
            if product.standard_price_date_lock and product.standard_price_date_lock > date.today():
                continue

            product.standard_price_date_lock = False
            product.with_delay(channel='root.standardprice').job_queue_standard_price_update(data['__domain'])


    @job
    @api.multi
    def job_queue_standard_price_update(self, data):

        OrderLine = self.env['sale.order.line']
        lines = OrderLine.search(data, order="id desc")
        partners = lines.mapped('order_id.partner_id')
        partner_count = len(partners)
        partner_count_company = self.env.user.company_id.partner_count or 0
        if partner_count >= partner_count_company:
            price = sum(
                [lines.filtered(lambda l: l.order_id.partner_id == partner)[:1].price_unit for partner in partners])
            if price:
                self.lst_price = (price / partner_count)
        else:
            self.lst_price = self.categ_id.standard_price
        return True


ProductProduct()
