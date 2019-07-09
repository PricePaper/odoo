# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import UserError


class UpdateVendorPricelist(models.TransientModel):

    _name = 'update.vendor.pricelist'


    vendor_id = fields.Many2one('res.partner', string='Vendor')
    line_ids = fields.One2many('update.vendor.pricelist.line', 'parent_id', string='Lines')



    @api.onchange('vendor_id')
    def onchange_vendor_id(self):
        self.ensure_one()
        self.line_ids.unlink()
        if self.vendor_id:
            pricelists = self.env['product.supplierinfo'].search([('name', '=', self.vendor_id.id)])
            res = []
            for ele in pricelists:
                vals = { 'pricelist_id': ele.id,
                         'product_id': ele.product_id and ele.product_id.id,
                         'qty_min': ele.min_qty,
                         'price': ele.price,
                        }
                res.append(vals)
            self.line_ids = res


    @api.multi
    def update_pricelists(self):
        self.ensure_one()
        for line in self.line_ids:
            if line.pricelist_id:
                line.pricelist_id.write({'product_id': line.product_id.id,
                                         'min_qty': line.qty_min,
                                         'price': line.price,
                                        })
            else:
                self.env['product.supplierinfo'].create({'product_id': line.product_id.id,
                                                         'product_tmpl_id': line.product_id.product_tmpl_id.id,
                                                         'min_qty': line.qty_min,
                                                         'price': line.price,
                                                         'name': line.parent_id.vendor_id.id,
                                                        })
        return True


UpdateVendorPricelist()

class UpdateVendorPricelistLines(models.TransientModel):

    _name = 'update.vendor.pricelist.line'

    parent_id = fields.Many2one('update.vendor.pricelist', string='Parent')
    pricelist_id = fields.Many2one('product.supplierinfo', string='Vendor Pricelist')
    product_id = fields.Many2one('product.product', string='Product')
    qty_min = fields.Integer(string="Min Quantity", default=1)
    price = fields.Float(string='Price')


UpdateVendorPricelistLines()
