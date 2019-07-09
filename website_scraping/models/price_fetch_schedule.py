from odoo import models, fields, api,_
from datetime import datetime

class PriceFetchSchedule(models.Model):
    _name = "price.fetch.schedule"

    product_sku_ref_id = fields.Many2one('product.sku.reference', string='Reference', readonly=True, required=True, ondelete='cascade')
    name = fields.Many2one(related='product_sku_ref_id.product_id', string='Product', readonly=True)
    queued_date = fields.Datetime(string='Queued On', readonly=True, default=datetime.now())
    competitor = fields.Selection(related='product_sku_ref_id.web_config.competitor', string='Competitor')
    in_exception = fields.Boolean(related='product_sku_ref_id.in_exception', string='Exception')


    @api.model
    def update_price_fetch_schedule_cron(self):
        """
        Called from the cron job to create
        scheduled tasks in system which will be
        called from the scraping script to fetch
        date
        """
        active_configs = self.env['product.sku.reference'].search([('in_exception', '=', False)])
        all_scheduled_task_ids = self.search([]).mapped('product_sku_ref_id').ids
        active_configs = active_configs.filtered(lambda con: con.id not in all_scheduled_task_ids)
        active_configs.schedule_price_update()



PriceFetchSchedule()
