# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class Inventory(models.Model):
    _inherit = "stock.inventory"

    vendor_id = fields.Many2one('res.partner', string='Vendor')
#    bin_prefix = fields.Char(string='Prefix')
#    bin_location_from = fields.Integer(string='From')
#    bin_location_To = fields.Integer(string='To')
    # include_transit = fields.Boolean(string='Include qty in transit', default=True)


    @api.model
    def _selection_filter(self):
        res = super(Inventory, self)._selection_filter()
        res.extend([('vendor', _('Based on Vendor'))])
        return res


    def _get_inventory_lines_values(self):

        locations = self.env['stock.location'].search([('id', 'child_of', [self.location_id.id])])
        # if self.include_transit:
        #     locations = self.env['stock.location'].search(['|', ('id', 'child_of', [self.location_id.id]), ('is_transit_location', '=', True)])
        domain = ' location_id in %s'
        args = (tuple(locations.ids),)

        vals = []
        Product = self.env['product.product']
        # Empty recordset of products available in stock_quants
        quant_products = self.env['product.product']
        # Empty recordset of products to filter
        products_to_filter = self.env['product.product']

        # case 0: Filter on company
        if self.company_id:
            domain += ' AND company_id = %s'
            args += (self.company_id.id,)

        #case 1: Filter on One owner only or One product for a specific owner
        if self.partner_id:
            domain += ' AND owner_id = %s'
            args += (self.partner_id.id,)
        #case 2: Filter on One Lot/Serial Number
        if self.lot_id:
            domain += ' AND lot_id = %s'
            args += (self.lot_id.id,)
        #case 3: Filter on One product
        if self.product_id:
            domain += ' AND product_id = %s'
            args += (self.product_id.id,)
            products_to_filter |= self.product_id
        #case 4: Filter on A Pack
        if self.package_id:
            domain += ' AND package_id = %s'
            args += (self.package_id.id,)
        #case 5: Filter on One product category + Exahausted Products
        if self.category_id:
            categ_products = Product.search([('categ_id', '=', self.category_id.id)])
            domain += ' AND product_id = ANY (%s)'
            args += (categ_products.ids,)
            products_to_filter |= categ_products

        #case 6: Filter on vendor
        if self.vendor_id:
            vendor_products = Product.search([('seller_ids', '!=', False)])
            vendor_products = vendor_products.filtered(lambda r: r.seller_ids[0].name.id == self.vendor_id.id)
            domain += ' AND product_id = ANY (%s)'
            args += (vendor_products.ids,)
            products_to_filter |= vendor_products

#        #case 7: Filter on bin_location
#        if self.bin_prefix:
#            bucket_location = []
#            for i in range(self.bin_location_from, self.bin_location_To+1):
#                bucket_location.append(self.bin_prefix+str(i))
#            bin_loc_products = Product.search([('bucket_location', 'in', bucket_location)])
#            domain += ' AND product_id = ANY (%s)'
#            args += (bin_loc_products.ids,)
#            products_to_filter |= bin_loc_products


        self.env.cr.execute("""SELECT product_id, sum(quantity) as product_qty, location_id, lot_id as prod_lot_id, package_id, owner_id as partner_id
            FROM stock_quant
            WHERE %s
            GROUP BY product_id, location_id, lot_id, package_id, partner_id """ % domain, args)

        for product_data in self.env.cr.dictfetchall():
            # replace the None the dictionary by False, because falsy values are tested later on
            for void_field in [item[0] for item in product_data.items() if item[1] is None]:
                product_data[void_field] = False
            product_data['theoretical_qty'] = product_data['product_qty']
            if product_data['product_id']:
                product_data['product_uom_id'] = Product.browse(product_data['product_id']).uom_id.id
                quant_products |= Product.browse(product_data['product_id'])
            vals.append(product_data)
        if self.exhausted:
            exhausted_vals = self._get_exhausted_inventory_line(products_to_filter, quant_products)
            vals.extend(exhausted_vals)
        return vals



    @api.onchange('filter')
    def onchange_filter(self):
        res = super(Inventory, self).onchange_filter()
        if self.filter != 'vendor':
            self.vendor_id = False
        return res

Inventory()

#class InventoryLine(models.Model):
#    _inherit = "stock.inventory.line"

#    bucket_location = fields.Char(string='Bin Location', related='product_id.bucket_location')

#InventoryLine()
