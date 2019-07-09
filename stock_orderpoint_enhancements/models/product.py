# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
import datetime
from dateutil.relativedelta import *
import calendar
from math import ceil, floor
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError
import logging as server_log
import calendar
from odoo.addons.queue_job.job import job

to_date_hardcoded = datetime.datetime.strptime('2017-12-28', '%Y-%m-%d').date()

class ProductProduct(models.Model):
    _inherit = 'product.product'

    last_op_update_date = fields.Datetime(string='Last Orderpoint Update Date')
    forecast_days = fields.Integer(string="Forecast Days", default=30)
    orderpoint_update_date = fields.Date(string='Orderpoint Update Date')
    dont_use_fbprophet = fields.Boolean(string='Do not use Fbprophet Forecasting')
    past_days = fields.Integer(string="Fbprophet Hist Days", help="Days worth of historical data to be taken into consideration for Fbprophet calculation", default=1825)
#    real_forecast_qty = fields.Float(string='Real Forecast Qty', compute='compute_real_forecast_qty')


#    @api.multi
#    def compute_real_forecast_qty(self, prophet_start_date=''):
#        """
#        Fb Prophet test harness
#        shows the real quantity of products sold and fbprophet forecast
#        using past data based on prophet_start_date key in system parameters
#        and forecast_days field set in product ie: if 2018-02-28 set in system param
#        and 30 set as forecast_days in product form, then this methord
#        will tell the actual quantity sold and forecasted quantity according to
#        fb prophet for the date range 2018-02-28 - 2018-03-30
#        """
#        for pro in self:
#            qty = 0
#            for_quantity = 0
#            for_quantity_min = 0
#            for_quantity_max = 0
#            from_flag = True
#            if isinstance(prophet_start_date, dict):
#                from_flag = False
#                prophet_start_date = pro.env['ir.config_parameter'].sudo().get_param('prophet_start_date')

#            start_date = prophet_start_date and datetime.datetime.strptime(prophet_start_date, '%Y-%m-%d').date() or False
#            if start_date and start_date <= datetime.date.today():
#                to_date = start_date + relativedelta(days=pro.forecast_days)


#                product_ids = [pro.id]
#                forecast = []
#                if pro.superseded:
#                    product_ids.append(pro.superseded.id)
#                query = """
#                        SELECT sum(l.product_uom_qty), l.product_uom from sale_order o, sale_order_line
#                        l WHERE o.date_order > '%s'
#                        AND o.date_order <= '%s' AND o.id=l.order_id AND
#                        l.product_id in (%s) AND l.product_uom_qty>0 AND o.state IN ('sale', 'done') GROUP BY l.product_uom;""" % (str(start_date),str(to_date), (",".join(str(x) for x in product_ids)))
#                self.env.cr.execute(query)
#                result = self.env.cr.fetchall()
#                for product_uom_qty in result:
#                    if product_uom_qty[1] == pro.uom_id.id:
#                        qty += product_uom_qty[0]
#                    else:
#                        sale_uom_factor = self.env['product.uom'].browse(product_uom_qty[1]).factor
#                        qty += ((product_uom_qty[0] * pro.uom_id.factor) / sale_uom_factor)

#            periods = pro.forecast_days or 31
#            forecast = pro.forecast_sales(periods=periods, freq='d', to_date=str(start_date))
#            range_end = start_date+relativedelta(days=periods)
#            flag = False
#            for ele in forecast:
#                if datetime.datetime.strptime(ele[0], '%Y-%m-%d').date() >= start_date:
#                    flag = True
#                if flag:
#                    for_quantity += ele[1] # quantity,
#                    for_quantity_min += ele[2] #min_quantity,
#                    for_quantity_max += ele[3] # max_quantity,
#            if from_flag:
#                return {'start_date': str(start_date),
#                        'end_date': str(range_end),
#                        'real_qty': str(round(qty,2)),
#                        'forecasted': str(round(for_quantity,2)),
#                        'forecasted_max': str(round(for_quantity_max,2)),
#                        'forecasted_min': str(round(for_quantity_min,2)),
#                        'product_sku': str(pro.default_code),
#                        'product_name': str(pro.name),
#                        'UOM': pro.uom_id.name,
#                       }

#            raise UserError("Evaluation Period: %s - %s\nReal Qty: %s %s\n Forecasted: %s %s\n Forecasted Max: %s %s\n Forecasted Min: %s %s" %(str(start_date), str(range_end), qty, pro.uom_id.name, round(for_quantity,2), pro.uom_id.name, round(for_quantity_max, 2), pro.uom_id.name, round(for_quantity_min,2 ), pro.uom_id.name))


    @api.multi
    def get_fbprophet_config(self):
        """
        Return specific fbprophet configuration
        """

        config = self.env['fbprophet.config'].search([('config_type', '=', 'inventory')]) or False

        product_config = config.filtered(lambda r : r.inv_config_for == 'product' and r.product_id == self)
        if product_config:
            return product_config[0]
        categ_config = config.filtered(lambda r : r.inv_config_for == 'categ' and r.categ_id == self.categ_id)
        if categ_config:
            return categ_config[0]
        global_config = config.filtered(lambda r : r.inv_config_for == 'global')
        if global_config:
            return global_config[0]

        config = self.env['fbprophet.config'].search([('config_type', '=', 'default')], limit=1) or False
        return config



    @api.multi
    def forecast_sales(self, periods=30, freq='d', to_date = str(datetime.date.today())):
        """
        Forecast the sale of a product in daily basis by collecting
        past 5 years sales details
        """

        to_date = datetime.datetime.strptime(to_date, "%Y-%m-%d").date()
        if periods == 30 and freq == 'd':
            forecast_from = (to_date+relativedelta(days=1))

            month_last_date = calendar.monthrange(forecast_from.year, forecast_from.month)[1]
            periods = month_last_date

        self.ensure_one()
        config = self.get_fbprophet_config()
        # to_date = datetime.date.today()
        from_date = (to_date-relativedelta(days=self.past_days)).strftime('%Y-%m-%d')
        product_ids = [self.id]
        forecast = []
        if self.superseded:
            product_ids.append(self.superseded.id)
        query = """
                SELECT to_char(o.date_order, 'YYYY-MM-DD')as
                year_month_day, sum(l.product_uom_qty), l.product_uom from sale_order o, sale_order_line
                l WHERE o.date_order >= '%s'
                AND o.date_order <= '%s' AND o.id=l.order_id AND
                l.product_id in (%s) AND l.product_uom_qty>0 AND o.state IN ('sale', 'done') GROUP BY l.product_uom, year_month_day ORDER BY year_month_day;""" % (from_date,str(to_date), (",".join(str(x) for x in product_ids)))

        self.env.cr.execute(query)
        result = self.env.cr.fetchall()
        if result:
            result = self.filler_to_append_zero_qty(result, to_date)
            date_to = (to_date + relativedelta(days=periods)).strftime('%Y-%m-%d')
            try:
                forecast = self.env['odoo_fbprophet.prophet.bridge'].run_prophet(result, from_date, date_to, periods=periods, freq=freq, config=config)
            except:
                server_log.error("No data available for the product %s to forecast sales" % (self.name))
        else:
            server_log.error("No data available for the product %s to forecast sales" % (self.name))
        return forecast

    @api.model
    def get_qty_from_orders(self, product_id, forecast_begin):
        to_date = datetime.datetime.strptime(forecast_begin, "%Y-%m-%d").date()
        forecast_end = (to_date + relativedelta(months=1)).strftime('%Y-%m-%d')
        orders = self.env['sale.order'].search([('confirmation_date', '>', forecast_begin), ('confirmation_date', '<', str(forecast_end))])
        qty = 0.00
        for order in orders:
            for line in order.order_line:
                if line.product_id and line.product_id.id == product_id:
                    if line.product_uom == line.product_id.uom_id:
                        qty += line.product_uom_qty
                    else:
                        sale_uom_factor = line.product_uom.factor
                        qty += ((line.product_uom_qty * self.uom_id.factor) / sale_uom_factor)
        return qty


    @api.multi
    def show_forecast(self):
        """
        Return a graph and pivot views which are
        ploted with the forecast result
        """
        prophet_start_date = self.env['ir.config_parameter'].sudo().get_param('prophet_start_date')
        to_date = prophet_start_date and datetime.datetime.strptime(prophet_start_date, '%Y-%m-%d').date() or datetime.date.today()
        self.ensure_one()
        periods = self.forecast_days or 31
        forecast = self.forecast_sales(periods=periods, freq='d', to_date=str(to_date))
        self.env['product.forecast'].search([]).unlink()
        flag = False
        count = 0
        for ele in forecast:
            if datetime.datetime.strptime(ele[0], '%Y-%m-%d').date() >= to_date:
                flag = True
            if flag:
                count+=1
                self.env['product.forecast'].create({'product_id': self.id,
                                                     'date': ele[0],
                                                     'quantity': ele[1], # quantity,
                                                     'quantity_min': ele[2], #min_quantity,
                                                     'quantity_max': ele[3], # max_quantity,
                                                    })

#        if count>45:
#            raise ValidationError(_("Graphical representation is not possible due to large data,Please minimize forecast days"))

        graph_id  = self.env.ref('stock_orderpoint_enhancements.view_order_product_forecast_graph').id
        pivot_id = self.env.ref('stock_orderpoint_enhancements.view_order_product_forecast_pivot').id
        res = {
            "type": "ir.actions.act_window",
            "name" : "Sale Forecast",
            "res_model": "product.forecast",
            "views": [[graph_id, "graph"], [pivot_id, "pivot"]],
            "domain": [["product_id", "=", self.id]],
            "target": "current",
        }

        return res




    @api.model
    def filler_to_append_zero_qty(self, result, to_date):
        """
        Process result of query by adding missing days
        with qty(0.0) between start_date and to_date
        Converts uom_qty into base uom_qty
        """
        res = []
#        to_date = datetime.date.today()
#        start_date = (to_date-relativedelta(years=3)).replace(day=1)
        start_date = result and result[0] and result[0][0]
        start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()


        while(start_date <= to_date):
            val = start_date.strftime("%Y-%m-%d")
            in_list = [rec for rec in result if rec and str(rec[0]) == val]
            if start_date.weekday() not in (5,6):
                if not in_list:
                    res.append((val,0.0))
                else:
                    qty = 0
                    for product_uom_qty in in_list:
                        if product_uom_qty[2] == self.uom_id.id:
                            qty += product_uom_qty[1]
                        else:
                            sale_uom_factor = self.env['product.uom'].browse(product_uom_qty[2]).factor
                            qty += ((product_uom_qty[1] * self.uom_id.factor) / sale_uom_factor)
                    res.append((val,qty))
            start_date = start_date + relativedelta(days=1)
        return res


    @api.multi
    def calculate_qty(self, forecast, to_date, to_date_plus_delay):
        flag = False
        quantity = 0
        for ele in forecast:
            if datetime.datetime.strptime(ele[0], '%Y-%m-%d').date() >= to_date:
                flag = True
            if flag and ele[0] <= str(to_date_plus_delay):#calculate min and max qty between to_date and to_date_plus_delay
                quantity += ele[1]
        if quantity and self.env.user.company_id.buffer_percetage:
            quantity = quantity * ((100+self.env.user.company_id.buffer_percetage)/100)
        return quantity


    @api.multi
    @job
    def job_queue_forecast(self):
        """
        cron method to set the orderpoints(OP) for every products
        uses fbprophet based forecasting for the OP setup.
        """

        prophet_start_date = self.env['ir.config_parameter'].sudo().get_param('prophet_start_date')
        to_date = prophet_start_date and datetime.datetime.strptime(prophet_start_date, '%Y-%m-%d').date() or datetime.date.today()

        vendor = self.seller_ids
        if not vendor:
            server_log.error('Supplier is not set for product %s' % self.name)
        else:
            delivery_lead_time = vendor and self.seller_ids[0].delay or 0
            if not delivery_lead_time:
                delivery_lead_time = vendor and self.seller_ids[0].name.delay or 0
                if not delivery_lead_time:
                    server_log.error('Delivery lead time is not available for product %s' % self.name)

            max_delivery_lead_time = delivery_lead_time + (vendor and self.seller_ids[0].name.order_freq or 0)

            to_date_plus_delay = to_date + relativedelta(days=delivery_lead_time)
            max_to_date_plus_delay = to_date + relativedelta(days=max_delivery_lead_time)


            min_forecast = self.forecast_sales(periods=delivery_lead_time, freq='d', to_date=str(to_date))
            min_quantity = self.calculate_qty(min_forecast, to_date, to_date_plus_delay)

            max_quantity = min_quantity
            if delivery_lead_time != max_delivery_lead_time:
                max_forecast = self.forecast_sales(periods=max_delivery_lead_time, freq='d', to_date=str(to_date))
                max_quantity = self.calculate_qty(max_forecast, to_date, max_to_date_plus_delay)

            orderpoint = self.orderpoint_ids and self.orderpoint_ids[0] or False

            if orderpoint:
                if not self.orderpoint_update_date or self.orderpoint_update_date < str(datetime.date.today()):
                    orderpoint.write({'product_min_qty': ceil(min_quantity),
                                      'product_max_qty': ceil(max_quantity),
                                     })
            else:
                self.env['stock.warehouse.orderpoint'].create({
                                                               'product_id': self.id,
                                                               'product_min_qty': min_quantity,
                                                               'product_max_qty': max_quantity,
                                                               'qty_multiple': 1,
                                                               'product_uom': self.uom_id.id,
                                                              })
            self.last_op_update_date = str(datetime.datetime.today())
        return True


    @api.model
    def set_orderpoint_cron(self):
        """
        cron method to set the orderpoints(OP) for every products
        uses fbprophet based forecasting for the OP setup.
        """

        products = self.env['product.product'].search([('active','=',True), ('type', '=', 'product'), ('dont_use_fbprophet', '=', False)], order='last_op_update_date')
        for product in products:
            product.with_delay(channel='root.Product Orderpoint').job_queue_forecast()




ProductProduct()




class  SupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'

#    delay = fields.Integer(
#        string='Delivery Lead Time', related='name.delay', required=True, store=True,
#        help="Lead time in days between the confirmation of the purchase order and the receipt of the products in your warehouse. Used by the scheduler for automatic computation of the purchase order planning.")


    @api.multi
    def write(self, values):
        """
        Overriding write method to track changes in delivery lead time and
        reset orderpoint min/max qty according to delivery lead time
        """

        res = super(SupplierInfo, self).write(values)
        if 'delay' in values:
            product = self.product_id or self.env['product.product'].browse(self.product_tmpl_id.product_variant_id[0].id)
            self.reset_orderpoint(product)
        return res


    @api.multi
    def reset_orderpoint(self, product):
        """
        Reset min_qty and max_quantity in orderpoints
        based on the updated delivery lead time
        """
        self.ensure_one()

        prophet_start_date = self.env['ir.config_parameter'].sudo().get_param('prophet_start_date')
        to_date = prophet_start_date and datetime.datetime.strptime(prophet_start_date, '%Y-%m-%d').date() or datetime.date.today()
        forecast = product.forecast_sales(periods=30, freq='d', to_date=str(to_date))







        orderpoint = product.orderpoint_ids and product.orderpoint_ids[0] or False
        delivery_lead_time = self.delay or self.name and self.name.delay
        to_date_plus_delay = to_date + relativedelta(days=delivery_lead_time)
        flag = False
        min_quantity = 0
        max_quantity = 0
        for ele in forecast:
            if ele[0] >= str(to_date):
                flag = True
            if flag and ele[0] <= str(to_date_plus_delay):
                min_quantity += ele[1]
                max_quantity += ele[3]
        if orderpoint:
            orderpoint.write({'product_min_qty': ceil(min_quantity),
                              'product_max_qty': ceil(max_quantity),
                             })
            product.last_op_update_date = str(datetime.datetime.today())


SupplierInfo()
