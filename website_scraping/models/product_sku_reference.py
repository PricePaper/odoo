from odoo import models, fields, api,_

class ProductSkuReference(models.Model):
    _name = "product.sku.reference"
    _inherit = ['mail.thread']

    product_id = fields.Many2one('product.product', string='Product')
    competitor_sku = fields.Char(string='Competitor SKU')
    competitor_desc = fields.Char(string='Competitor description')
    website_link = fields.Char(string='URL')
    qty_in_uom = fields.Float(string='Units in UOM')
    competitor = fields.Selection([('rdepot', 'Restaurant Depot'), ('wdepot', 'Webstaurant Depot')], related='web_config.competitor', string='Competitor')
    web_config = fields.Many2one('website.scraping.cofig', string='Competitor')
    scheduled_ids = fields.One2many('price.fetch.schedule', 'product_sku_ref_id', string='Scheduled Price Fetches')
    in_exception = fields.Boolean(string='Exception', default=False)

    @api.multi
    @api.depends('product_id', 'competitor')
    def name_get(self):
        result = []
        for record in self:
            name = "%s_%s" % (record.product_id and record.product_id.name , record.competitor and dict(self._fields['competitor'].selection(record)).get(record.competitor) or '')
            result.append((record.id,name))
        return result

    @api.multi
    def schedule_price_update(self):
        """
        creates a scheduled task in the system
        """
        for rec in self:
            if not rec.in_exception:
                self.env['price.fetch.schedule'].create({'product_sku_ref_id':rec.id})

    @api.multi
    def mark_exception_fixed(self):
        for rec in self:
            rec.in_exception = False
            rec.message_post(body="Exception Removed")


    @api.model
    def log_exception_error(self, ref_id, except_string="Exception Error"):
        ref_obj = self.env['product.sku.reference'].browse(ref_id)
        ref_obj.in_exception = True
        ref_obj.message_post(body=except_string)
        return True


ProductSkuReference()
