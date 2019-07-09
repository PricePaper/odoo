from odoo import models, fields, api,_
from odoo.exceptions import UserError


class DriverInvoiceWizard(models.TransientModel):

    _name = 'driver.invoice.wizard'

    amount = fields.Float(string='Invoice Amount')

    @api.multi
    def create_invoice(self):

        batches = self.env['stock.picking.batch'].browse(self._context.get('active_ids'))


        # product = self.env['product.product'].search([('default_code', '=', 'batch_driver_invoice')])
        payment_term = self.env['ir.model.data'].get_object_reference('account', 'account_payment_term_immediate')[1]
        product_id = self.env['ir.model.data'].get_object_reference('batch_delivery', 'batch_picking_driver_invoice')[1]
        product = self.env['product.product'].browse(product_id)
        account_id = False
        if product.id:
            account_id = product.property_account_income_id.id
        if not account_id:
            raise UserError(
                _('There is no income account defined for this product: "%s". You may have to install a chart of account from Accounting app, settings menu.') %
                (product.name,))


        for batch in batches:
            invoice = self.env['account.invoice']
            partner_id = batch.truck_driver_id
            vals = {
                    'partner_id':partner_id.id,
                    'account_id':partner_id.property_account_receivable_id.id,
                    'type': 'out_invoice',
                    'payment_term_id': payment_term,
                    'invoice_line_ids': [(0, 0, {
                        'name': 'Batch %s Driver Invoice'%(batch.name),
                        'origin': batch.name,
                        'account_id': account_id,
                        'price_unit': self.amount,
                        'quantity': 1.0,
                        'discount': 0.0,
                        'uom_id': product.uom_id.id,
                        'product_id': product.id,
                    })],
                    }
            invoice_id = invoice.create(vals)
            # invoice_id.action_invoice_open()
            batch.invoice_id = invoice_id.id


DriverInvoiceWizard()
