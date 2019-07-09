from odoo import models, fields, api,_

class CompetitorItems(models.Model):
    _name = "competitor.website.price"

    product_sku_ref_id = fields.Many2one('product.sku.reference', string='Reference')
    item_name = fields.Char(string='Competitor Item Name')
    item_price = fields.Float(String='Competitor Price')
    price = fields.Float(compute='get_price', string='Unit Price')
    competitor_item_uom = fields.Float(string='Competitor Units in UOM', related='product_sku_ref_id.qty_in_uom', readonly=True)
    update_date = fields.Datetime(string='Updated On')
    product_id = fields.Many2one(related='product_sku_ref_id.product_id', string='Product', readonly=True)
    competitor = fields.Selection(related='product_sku_ref_id.web_config.competitor', string='Competitor')
    active = fields.Boolean(string='Active', default=True)


    @api.depends('item_price')
    def get_price(self):
        for record in self:
            if record.product_sku_ref_id.qty_in_uom:
                record.price = (record.item_price / record.competitor_item_uom) * record.product_id.uom_id.factor_inv

    @api.multi
    @api.depends('product_sku_ref_id')
    def name_get(self):
        result = []
        for record in self:
            name = "%s_%s" % (record.product_sku_ref_id and record.product_sku_ref_id.product_id.name , record.product_sku_ref_id and dict(self.product_sku_ref_id._fields['competitor'].selection(record.product_sku_ref_id)).get(record.product_sku_ref_id.competitor) or '')
            result.append((record.id,name))
        return result


    @api.model
    def create(self, vals):
        res = super(CompetitorItems, self).create(vals)
        res.update_competitor_pricelist()
        return res



    @api.multi
    def update_competitor_pricelist(self):
        for rec in self:
            pricelists = self.env['product.pricelist'].search([('type', '=', 'competitor'), ('competitor_id', '=', rec.product_sku_ref_id.web_config.id)])
            for pricelist in pricelists:
                lines = pricelist.customer_product_price_ids.filtered(lambda p: p.product_id.id == rec.product_id.id)
                price = rec.price + (rec.price * pricelist.competietor_margin/100)

                for line in lines:
                    line.write({'price': price,
                                'product_uom': rec.product_id.uom_id.id,
                               })
                if not lines:
                    self.env['customer.product.price'].create({'pricelist_id': pricelist.id,
                                                               'product_id': rec.product_id.id,
                                                               'price': price,
                                                               'product_uom': rec.product_id.uom_id.id,
                                                              })
        return True

CompetitorItems()
