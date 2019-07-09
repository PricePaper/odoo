# -*- coding: utf-8 -*-

from odoo import models, fields, registry, api,_
from datetime import datetime,date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta
import pytz
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.addons import decimal_precision as dp

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    release_date = fields.Date(string="Earliest Delivery Date", default=lambda s: s.get_release_deliver_default_date())
    deliver_by = fields.Date(string="Deliver By", default=lambda s: s.get_release_deliver_default_date())
    is_creditexceed = fields.Boolean(string="Credit limit exceeded", default=False, copy=False)
    credit_warning = fields.Text(string='Warning Message', compute='compute_credit_warning', copy=False)
    ready_to_release = fields.Boolean(string="Ready to release", default=False, copy=False)
    gross_profit = fields.Monetary(compute='calculate_gross_profit', string='Gross Profit')
    is_quotation = fields.Boolean(string="Create as Quotation", default=False, copy=False)


    @api.model
    def get_release_deliver_default_date(self):
        user_tz = self.env.user.tz or "UTC"
        user_time = datetime.now(pytz.timezone(user_tz))
        user_time = user_time + relativedelta(days=1)
        return user_time


    @api.onchange('partner_shipping_id')
    def onchange_partner_id_carrier_id(self):
        if self.partner_shipping_id:
            self.carrier_id = self.partner_shipping_id and self.partner_shipping_id.property_delivery_carrier_id or self.partner_id and self.partner_id.property_delivery_carrier_id
        else:
            self.partner_id and self.partner_id.property_delivery_carrier_id


    @api.onchange('carrier_id','order_line')
    def onchange_delivery_carrier_method(self):
        """ onchange delivery carrier,
            recompute the delicery price
        """
        if self.carrier_id:
            self.get_delivery_price()


    @api.multi
    def write(self, vals):
        """
        auto save the delivery line.
        """
        res = super(SaleOrder, self).write(vals)
        self.check_payment_term()
        for order in self:
            if order.carrier_id:
                order.adjust_delivery_line()
            else:
                order._remove_delivery_line()
        return res



    def get_delivery_price(self):
        """
        overriden to bypass the delivery price get block for confirmed orders
        """
        for order in self.filtered(lambda o: o.state in ('draft', 'sent', 'sale') and len(o.order_line) > 0):
            # or on an SO that has no lines yet
            order.delivery_rating_success = False
            res = order.carrier_id.rate_shipment(order)
            if res['success']:
                order.delivery_rating_success = True
                order.delivery_price = res['price']
                order.delivery_message = res['warning_message']
            else:
                order.delivery_rating_success = False
                order.delivery_price = 0.0
                order.delivery_message = res['error_message']

    @api.multi
    def adjust_delivery_line(self):
        """
        method written to adjust delivery charges line in order line
        upon form save with changes in delivery method in sale order record
        """
        for order in self:
#            if not order.delivery_rating_success and order.order_line:
#                raise UserError(_('Please use "Check price" in order to compute a shipping price for this quotation.'))

            price_unit = order.carrier_id.rate_shipment(order)['price']
            delivery_line = self.env['sale.order.line'].search([('order_id', '=', order.id), ('is_delivery', '=', True)])
            if not delivery_line and order.order_line:
                # TODO check whether it is safe to use delivery_price here
                order._create_delivery_line(order.carrier_id, price_unit)

            if delivery_line:

                # Apply fiscal position to get taxes to be applied
                taxes = order.carrier_id.product_id.taxes_id.filtered(lambda t: t.company_id.id == order.company_id.id)
                taxes_ids = taxes.ids
                if order.partner_id and order.fiscal_position_id:
                    taxes_ids = order.fiscal_position_id.map_tax(taxes, order.carrier_id.product_id, order.partner_id).ids

                #reset delivery line
                delivery_line.product_id = order.carrier_id.product_id.id
                delivery_line.price_unit = price_unit
                delivery_line.name = order.carrier_id.name
                delivery_line.product_uom_qty = 1
                delivery_line.product_uom = order.carrier_id.product_id.uom_id.id

        return True


    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        res = super(SaleOrder, self).onchange_partner_id()
        if self.partner_id:
            shipping_date = date.today() + relativedelta(days=1)
            day_list = []
            if self.partner_id.delivery_day_mon:
                day_list.append(0)
            if self.partner_id.delivery_day_tue:
                day_list.append(1)
            if self.partner_id.delivery_day_wed:
                day_list.append(2)
            if self.partner_id.delivery_day_thu:
                day_list.append(3)
            if self.partner_id.delivery_day_fri:
                day_list.append(4)
            if self.partner_id.delivery_day_sat:
                day_list.append(5)
            if self.partner_id.delivery_day_sun:
                day_list.append(6)
            weekday = date.today().weekday()
            day_diff = 0
            if day_list:
                if any(weekday < i for i in day_list):
                    for i in day_list:
                        if weekday < i:
                            day_diff = i - weekday
                            break
                else:
                    day_diff = (6 - weekday) + day_list[0] + 1
                shipping_date = date.today() + relativedelta(days=day_diff)
            self.release_date = shipping_date
            self.deliver_by = shipping_date
        return res


    @api.model
    def create(self, vals):
        """
        override to Confirm the sale order on creation
        unless field is_quotation set as true.

        """
        res = super(SaleOrder, self).create(vals)
        res.check_payment_term()
        if not res.credit_warning and not res.is_quotation:
            res.action_confirm()
        elif res.credit_warning and not res.is_quotation:
            res.write({'is_creditexceed':True, 'ready_to_release': False})
            res.message_post(body=res.credit_warning)
            msg=''
            for order_line in res.order_line:
                if order_line.profit_margin < 0.0 and not ('rebate_contract_id' in order_line and order_line.rebate_contract_id):
                    msg = msg+'[%s]%s ' % (order_line.product_id.default_code,order_line.product_id.name) + "Unit Price is less than  Product Cost Price\n"
            if msg:
                team = self.env['helpdesk.team'].search([('is_sales_team', '=', True)], limit=1)
                if team:
                    vals = {'name': 'Sale order with Product below working cost',
                            'team_id': team and team.id,
                            'description': 'Order : ' + res.name + '\n' + msg,
                            }
                    ticket = self.env['helpdesk.ticket'].create(vals)
        return res


    @api.depends('order_line.profit_margin')
    def calculate_gross_profit(self):
        """
        Compute the gross profit of the SO.
        """
        for order in self:
            gross_profit = 0
            for line in order.order_line:
                if line.is_delivery:
                    gross_profit += line.price_subtotal
                    gross_profit -= order.carrier_id.average_company_cost
                else:
                    gross_profit += line.profit_margin
            order.update({'gross_profit' : round(gross_profit,2)})



    @api.constrains('release_date')
    def get_release_date_warning(self):

        if self.release_date and self.release_date > str(date.today()+timedelta(days=+6)):
            raise ValidationError(_('Earliest Delivery Date is greater than 1 week'))

        if self.release_date and self.release_date < str(date.today()):
            raise ValidationError(_('Earliest Delivery Date should be greater than Current Date'))




    def compute_credit_warning(self):

        for order in self:
            debit_due = self.env['account.move.line'].search([('partner_id', '=', order.partner_id.id),('full_reconcile_id', '=', False), ('debit', '!=', False), ('date_maturity_grace', '<', date.today())], order='date_maturity_grace desc')
            msg = ''
            if order.partner_id.credit_limit and (order.partner_id.credit + order.amount_total > order.partner_id.credit_limit):
                msg = "Customer Credit limit Exceeded.\n%s's Credit limit is %s and due amount is %s\n" %(order.partner_id.name,order.partner_id.credit_limit,(order.partner_id.credit + order.amount_total))
            if debit_due:
                msg = msg + 'Customer has pending invoices.'
                for rec in debit_due:
                    msg = msg + '\n%s' %(rec.invoice_id.number)
            for order_line in order.order_line:
                if order_line.profit_margin < 0.0 and not ('rebate_contract_id' in order_line and order_line.rebate_contract_id):
                    msg = msg + '[%s]%s ' % (order_line.product_id.default_code,order_line.product_id.name) + "Unit Price is less than  Product Cost Price"


            self.credit_warning = msg

    @api.multi
    def action_ready_to_release(self):
        """
        release the bolcked sale order.
        """
        for order in self:
            order.ready_to_release = True


    def check_credit_limit(self):
        """
        wheather the partner's credit limit exceeded or
        partner has pending invoices block the sale order confirmation
        and display warning message.
        """

        for order in self:
            msg = order.credit_warning and order.credit_warning or ''
            with api.Environment.manage():
                new_cr = self.pool.cursor()
                so = order.with_env(order.env(cr=new_cr))
                if msg:
                    so.write({'is_creditexceed':True, 'ready_to_release': False})
                    so.message_post(body=msg)
                else:
                    order.write({'is_creditexceed':False, 'ready_to_release': True})
                new_cr.commit()
                new_cr.close()
            if msg:
                raise ValidationError(_(msg))
            else:
                return True


    @api.onchange('payment_term_id')
    def onchange_payment_term(self):
        user = self.env.user
        for order in self:
            partner_payment_term = order.partner_id and order.partner_id.property_payment_term_id
            if (order.payment_term_id.id != partner_payment_term.id) and not user.has_group('account.group_account_manager'):
                order.payment_term_id = partner_payment_term.id
                return {'warning': {'title': _('Invalid Action!'),'message' : "You dont have the rights to change the payment terms of this customer."}}




    @api.multi
    def check_payment_term(self):
        """
        Can only proceed with order if payment term is set
        """
        user = self.env.user
        for order in self:
            if not order.payment_term_id:
                raise ValidationError(_('Payment term is not set for this order please set to proceed.'))







    @api.multi
    def action_confirm(self):
        """
        create record in customer.price.history
        and also update the customer pricelist if needed
        """

        if not self.ready_to_release:
            self.check_credit_limit()
        res = super(SaleOrder, self).action_confirm()

        for order in self:
            for order_line in order.order_line:
                order_line.update_price_list()
        return res

    @api.multi
    def add_purchase_history_to_so_line(self):
        """
        Return 'add purchase history to so wizard'
        """
        line_ids1 = self.env['sale.order.line'].search(['|', '&', ('shipping_id','=', self.partner_shipping_id.id), ('is_last', '=', True), '&', ('order_id.validity_date', '>=', str(date.today())), ('order_id.state', '=', 'draft')])
        context ={'line_ids1' : line_ids1.ids}
        view_id = self.env.ref('price_paper.view_purchase_history_add_so_wiz').id
        return {
            'name': _('Add purchase history to SO'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'add.purchase.history.so',
            'view_id': view_id,
            'type': 'ir.actions.act_window',
            'context' : context,
            'target' :'new'
        }


SaleOrder()


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    profit_margin = fields.Monetary(compute='calculate_profit_margin', string="Profit")
    price_from = fields.Many2one('customer.product.price', string='Product Pricelist')
    last_sale = fields.Text(compute='compute_last_sale_detail', string='Last sale details', store=False)
    # color = fields.Text(compute='calculate_profit_margin', string="Color", store=False)
    product_onhand = fields.Float(string='Product Qty Available', related='product_id.virtual_available', digits=dp.get_precision('Product Unit of Measure'))
    new_product = fields.Boolean(string='New Product', copy=False)
    manual_price = fields.Boolean(string='Manual Price Change', copy=False)
    is_last = fields.Boolean(string='Is last Purchase')
    shipping_id = fields.Many2one(related='order_id.partner_shipping_id', string='Shipping Address')
    note = fields.Text('Note')
    note_type = fields.Selection(string='Note Type', selection=[('permanant', 'Save note'), ('temporary', 'Temporary Note')], default='temporary')
    lst_price = fields.Float(string='Standard Price', digits=dp.get_precision('Product Price'), store=True, compute='_compute_lst_cost_prices')
    confirmation_date = fields.Datetime(related='order_id.confirmation_date', string='Confirmation Date')
    working_cost = fields.Float(string='Working Cost', digits=dp.get_precision('Product Price'), store=True, compute='_compute_lst_cost_prices')



    @api.depends('product_id')
    def _compute_lst_cost_prices(self):
        for line in self:
            if line.product_id.lst_price:
                line.lst_price = line.product_id.lst_price
            if line.product_id.cost:
                line.working_cost = line.product_id.cost

    @api.multi
    def unlink(self):
        """
        lets users to bypass super unlink block for confirmed lines
        if line is delivery line
        """
        base = None
        unlinked_lines = self.env['sale.order.line']
        for parentClass in self.__class__.__bases__:
            if parentClass._name == 'base':
                base = parentClass

        for line in self:
            if line.is_delivery and base:
                base.unlink(line)
                unlinked_lines|= line
        return super(SaleOrderLine, self-unlinked_lines).unlink()


    @api.multi
    def name_get(self):

        result = []
        for line in self:
            result.append((line.id, "%s - %s - %s" % (line.name, line.product_uom.name, line.order_id.date_order)))
        return result




    def update_price_list(self):
        """
        Update pricelist
        """

        if not self.is_delivery and not self.is_downpayment:
            unit_price = self.price_unit
            if self.product_id.uom_id == self.product_uom and self.product_uom_qty % 1 != 0.0:
                numer = self.price_unit * self.product_uom_qty
                denom = (int(self.product_uom_qty / 1.0) + ((self.product_uom_qty % 1) * (100 + self.product_id.categ_id.repacking_upcharge) / 100))
                unit_price = round(numer / denom, 2)

            partner_history = self.env['sale.order.line'].search([('product_id', '=', self.product_id.id), ('shipping_id', '=', self.shipping_id.id), ('is_last', '=', True), ('product_uom', '=', self.product_uom.id)])
            partner_history and partner_history.write({'is_last': False})
            self.write({'is_last': True})

            #Create record in customer.product.price if not exist
            #if exist then check the price and update
            #if shared price exists then do not proceed with record creation

            if self.price_from and self.price_from.pricelist_id.type != 'competitor':
                if self.price_from.price < unit_price:
                    self.price_from.price = unit_price
                    self.manual_price = True
            else:
                prices_all = self.env['customer.product.price']
                for rec in self.order_id.partner_id.customer_pricelist_ids:
                    if rec.pricelist_id.type in ('shared', 'customer') and (not rec.pricelist_id.expiry_date or rec.pricelist_id.expiry_date >= str(date.today())):
                        prices_all |= rec.pricelist_id.customer_product_price_ids

                prices_all = prices_all.filtered(lambda r: r.product_id.id == self.product_id.id and r.product_uom.id == self.product_uom.id and (not r.partner_id or r.partner_id.id == self.order_id.partner_shipping_id.id))
                price_from = False
                for price_rec in prices_all:

                    if not price_rec.partner_id and prices_all.filtered(lambda r: r.partner_id):
                        continue

                    product_price = price_rec.price
                    price_from = price_rec
                    break
                if price_from:
                    if price_from.price < unit_price:
                        price_from.price = unit_price
                        self.manual_price = True

                else:
                    price_lists = self.order_id.partner_id.customer_pricelist_ids.filtered(lambda r: r.pricelist_id.type == 'customer').sorted(key=lambda r: r.sequence)

                    if not price_lists:
                        product_pricelist = self.env['product.pricelist'].create({
                                'name': self.order_id.partner_id.customer_code,
                                'type': 'customer',
                                })
                        price_lists = self.env['customer.pricelist'].create({
                                                                              'pricelist_id': product_pricelist.id,
                                                                              'partner_id': self.order_id.partner_id.id,
                                                                              'sequence': 0
                                                                              })
                    price_from = self.env['customer.product.price'].create({
                                                               'partner_id' : self.order_id.partner_shipping_id.id,
                                                               'product_id' : self.product_id.id,
                                                               'product_uom' : self.product_uom.id,
                                                               'pricelist_id': price_lists[0].pricelist_id.id,
                                                               'price': unit_price
                                                              })
                    self.new_product = True
                if price_from:
                    self.price_from = price_from.id



    @api.multi
    def write(self, vals):

        res = super(SaleOrderLine, self).write(vals)
        for line in self:
            if vals.get('price_unit') and line.order_id.state == 'sale':
                line.update_price_list()
        return res

    @api.model
    def create(self, vals):
        res = super(SaleOrderLine, self).create(vals)

        if res.order_id.state == 'sale':
            res.update_price_list()

        if res.note_type == 'permanant':
            note = self.env['product.notes'].search([('product_id', '=', res.product_id.id), ('partner_id', '=', res.order_id.partner_id.id)], limit=1)
            if not note:
                self.env['product.notes'].create({'product_id': res.product_id.id,
                                                  'partner_id': res.order_id.partner_id.id,
                                                  'notes': res.note
                                                  })
            else:
                note.notes = res.note
        return res


    @api.depends('product_id')
    def compute_last_sale_detail(self):
        """
        compute last sale detail of the product by the partner.
        """
        for line in self:
            if not line.order_id.partner_id:
                raise ValidationError(_('Please enter customer information first.'))
            line.last_sale = False
            if line.product_id:
                last = self.env['sale.order.line'].sudo().search([('order_id.partner_shipping_id', '=', line.order_id.partner_shipping_id and line.order_id.partner_shipping_id.id), ('product_id', '=', line.product_id.id), ('product_uom', '=', line.product_uom.id), ('is_last', '=', True)], limit=1)
                if last:
                    local = pytz.timezone(self.sudo().env.user.tz or "UTC")
                    last_date = datetime.strftime(pytz.utc.localize(datetime.strptime(last.order_id.confirmation_date, DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(local),"%m/%d/%Y %H:%M:%S")
                    line.last_sale = 'Order Date  - %s\nPrice Unit    - %s\nSale Order  - %s' %(last_date, last.price_unit, last.order_id.name)
                else:
                     line.last_sale = 'No Previous information Found'

    @api.depends('product_id', 'product_uom_qty', 'price_unit')
    def calculate_profit_margin(self):
        """
        Calculate profit margin for SO line
        """
        for line in self:
            if line.product_id:
                if line.is_delivery or line.is_downpayment:
                    line.profit_margin = 0.0
                else:
                    # product_price = line.product_uom and round(line.product_id.cost * line.product_id.uom_id.factor / line.product_uom.factor, 2) or 0
                    product_price = line.product_uom and round(line.working_cost * line.product_id.uom_id.factor / line.product_uom.factor, 2) or 0
                    line_price = line.price_unit
                    if line.product_id.uom_id != line.product_uom:
                        line_price = line.price_unit * (100/(100+ line.product_id.categ_id.repacking_upcharge))
                    elif line.product_id.uom_id == line.product_uom and line.product_uom_qty % 1 != 0.0:
                        numer = line.price_unit * line.product_uom_qty
                        denom = (int(line.product_uom_qty / 1.0) + ((line.product_uom_qty % 1) * (100 + line.product_id.categ_id.repacking_upcharge) / 100))
                        line_price = round(numer / denom, 2)

                    line.profit_margin = (line_price - product_price) * line.product_uom_qty
                # if line.profit_margin < 0.0:
                #     line.color = 'R'
                # elif line.profit_margin > 0.0:
                #     line.color = 'G'
                # else:
                #     line.color = 'B'

    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        """
        Add taxes automatically to sales lines if partner has a
        resale number and no taxes charged based on previous
        purchase history.
        Display a message from which pricelist the unit price is taken .

        """
        #TODO: update tax computational logic


        res = super(SaleOrderLine, self).product_id_change()
#        lst_price = 0
#        working_cost = 0
#        if not self.product_id:
#            res.update({'value' : {'lst_price': lst_price, 'working_cost': working_cost}})
        if self.product_id:
            warn_msg = not self.product_id.purchase_ok and "This item can no longer be purchased from vendors"  or ""
            partner_history = self.env['sale.order.line'].search([('order_id.partner_shipping_id', '=', self.order_id and self.order_id.partner_shipping_id.id), ('product_id', '=', self.product_id and self.product_id.id), ('is_last', '=', True)], limit=1)
            if self.order_id and self.order_id.partner_id.vat and partner_history and not partner_history.tax_id:
                self.tax_id = [(5, _, _)] # clear all tax values, no Taxes to be used

            #force domain the tax_id field with only available taxes based on applied fpos
            if not res.get('domain', False):
                res.update({'domain':{}})
            pro_tax_ids = self.product_id.taxes_id
            if self.order_id.fiscal_position_id:
                taxes_ids = self.order_id.fiscal_position_id.map_tax(pro_tax_ids, self.product_id, self.order_id.partner_id).ids
                res.get('domain', {}).update({'tax_id':[('id', 'in', taxes_ids)]})

            msg, product_price, price_from = self.calculate_customer_price()
            if msg:
                res.update({'warning': {'title': _('Warning!'),'message' : warn_msg and '%s\n%s' %(warn_msg,msg) or msg}})
            #standard price on sale order line
#            if self.product_id.lst_price:
#                lst_price = self.product_id.lst_price
#            if self.product_id.cost:
#                working_cost = self.product_id.cost

            res.update({'value' : {'price_unit' : product_price, 'price_from': price_from}}) # 'lst_price': lst_price, 'working_cost': working_cost}})
            # for uom only show those applicable uoms
            domain = res.get('domain', {})
            product_uom_domain = domain.get('product_uom', [])
            product_uom_domain.append(('id', 'in', self.product_id.sale_uoms.ids))

            # get this customers last time sale description for this product and update it in the line
            note = self.env['product.notes'].search([('product_id', '=', self.product_id.id), ('partner_id', '=', self.order_id.partner_id.id)], limit=1)
            if note:
                self.note = note.notes
            else:
                self.note = self.name
            # self._cr.execute("""select so.create_date, sol.name from sale_order_line sol join sale_order so ON (so.id = sol.order_id) where so.state != 'cancel' and so.partner_id=%s and sol.product_id=%s order by so.create_date desc limit 1""" % (self.order_id.partner_id.id, self.product_id.id))
            # data = self._cr.dictfetchall()
            # if data:
            #     self.name = data[0].get('name', '')
        return res


    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        """
        assign the price unit from customer_product_price
        based on the pricelist.
        If there is no pricelist assign the cost of product.
        """
        old_unit_price = self.price_unit
        res = super(SaleOrderLine, self).product_uom_change()
        warning, product_price, price_from = self.calculate_customer_price()
        if self._context.get('quantity', False):
            self.price_unit = old_unit_price
        else:
            self.price_unit = product_price
        self.price_from = price_from
        res = res and res or {}
        if self.product_uom_qty % 1 != 0.0:
            warning_mess = {
                'title': _('Fractional Qty Alert!'),
                'message' : _('You plan to sell Fractional Qty.')
            }
            res.update({'warning': warning_mess})
        return res



    @api.multi
    def calculate_customer_price(self):
        """
        Fetch unit price from the relevant pricelist of partner
        if product is not found in any pricelist,set
        product price as cost price of product
        """

        prices_all = self.env['customer.product.price']
        for rec in self.order_id.partner_id.customer_pricelist_ids:
            if not rec.pricelist_id.expiry_date or rec.pricelist_id.expiry_date >= str(date.today()):
                prices_all |= rec.pricelist_id.customer_product_price_ids

        prices_all = prices_all.filtered(lambda r: r.product_id.id == self.product_id.id and r.product_uom.id == self.product_uom.id and (not r.partner_id or r.partner_id.id == self.order_id.partner_shipping_id.id))
        product_price = 0.0
        price_from = False
        msg = ''
        for price_rec in prices_all:

            if price_rec.pricelist_id.type == 'customer' and not price_rec.partner_id and prices_all.filtered(lambda r: r.partner_id):
                continue

            if price_rec.pricelist_id.type not in ('customer', 'shared'):
                msg = "Unit price of this product is fetched from the pricelist %s." %(price_rec.pricelist_id.name)
            product_price = price_rec.price
            price_from = price_rec.id
            break
        if not price_from:
            if self.product_id and self.product_uom:
                product_price = self.product_id.uom_id._compute_price(self.product_id.list_price, self.product_uom) + self.product_id.price_extra

            msg = "Unit Price for this product is not found in any pricelists, fetching the unit price as product standard price."

            # broken UOM case add package breaking upcharge.
            if self.product_id.uom_id != self.product_uom and (self.product_id.uom_id.factor_inv > self.product_uom.factor_inv):
                product_price = product_price * ((100+self.product_id.categ_id.repacking_upcharge)/100)

        if self.product_id.uom_id == self.product_uom and self.product_uom_qty % 1 != 0.0:
            product_price = ((int(self.product_uom_qty / 1) * product_price) + ((self.product_uom_qty % 1) * product_price * ((100+self.product_id.categ_id.repacking_upcharge)/100))) / self.product_uom_qty

        return msg, product_price, price_from


SaleOrderLine()
