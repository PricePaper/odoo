# -*- coding: utf-8 -*-
from odoo import models, fields, api

from odoo.tools import float_is_zero


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    delivery_move_line_id = fields.Many2one(
        'stock.move.line', string='Delivery Move line For')
    delivery_picking_id = fields.Many2one(
        'stock.picking', string='Delivery for Picking', readonly=True, related='delivery_move_line_id.picking_id')
    pref_lot_id = fields.Many2one('stock.production.lot', string='Preferred Lot')
    is_transit = fields.Boolean(related='move_id.is_transit', readonly=True)

    @api.multi
    def write(self, vals):
        result = super(StockMoveLine, self).write(vals)
        for line in self:
            sale_line = line.move_id.sale_line_id

            if 'qty_done' in vals and sale_line:
                qty = vals['qty_done']
                invoice_lines = sale_line.invoice_lines.filtered(
                    lambda rec: rec.invoice_id.state != 'cancel' and line.move_id in rec.stock_move_ids)
                sale_line.qty_delivered = qty
                if invoice_lines:
                    invoice_lines.write({'quantity': qty})
                    invoice_lines.mapped('invoice_id').compute_taxes()
                else:
                    if len(line.move_id.picking_id.move_ids_without_package) != 1:
                        other_invoice_lines = line.move_id.picking_id.move_ids_without_package.mapped('sale_line_id').mapped('invoice_lines')
                        other_invoice_lines.filtered(
                            lambda rec: rec.invoice_id.state == 'draft')
                        if other_invoice_lines:
                            other_invoice = False
                            for ot_invoice_line in  other_invoice_lines:
                                if line.move_id.picking_id.id in ot_invoice_line.stock_move_ids.mapped('picking_id').ids:
                                    other_invoice = ot_invoice_line.mapped('invoice_id')
                                    continue
                            if other_invoice:
                                precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
                                if float_is_zero(sale_line.qty_to_invoice, precision_digits=precision):
                                    continue

                                if sale_line.qty_to_invoice > 0:
                                    inv_line = sale_line.invoice_line_create_vals(
                                        other_invoice.id, sale_line.qty_to_invoice
                                    )
                                    self.env['account.invoice.line'].create(inv_line)
                                other_invoice.compute_taxes()

            if 'picking_id' in vals:
                sale_line.invoice_lines.filtered(lambda rec: line.move_id in rec.stock_move_ids).sudo().unlink()

        return result

    @api.multi
    def unlink(self):
        for line in self:
            sale_line = line.move_id.sale_line_id
            if sale_line:
                invoice_lines = sale_line.invoice_lines.filtered(
                    lambda rec: rec.invoice_id.state != 'cancel' and line.move_id in rec.stock_move_ids)

                if invoice_lines:
                    invoices = invoice_lines.mapped('invoice_id')
                    invoice_lines.write({'quantity': 0})

        result = super(StockMoveLine, self).unlink()
        return result


StockMoveLine()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
