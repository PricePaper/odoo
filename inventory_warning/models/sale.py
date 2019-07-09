from odoo import fields, models, api, _
from datetime import datetime
from dateutil import relativedelta
from odoo.tools import float_compare



class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.model
    def create(self, vals):

        res = super(SaleOrderLine, self).create(vals)
        day = int(datetime.strftime(datetime.today(), '%w'))
        team = self.env['helpdesk.team'].search([('is_purchase_team', '=', True)], limit=1)
        if not team:
            return res

        for line in res:
            if line.product_id.type == 'product':
                precision = line.env['decimal.precision'].precision_get('Product Unit of Measure')
                product = line.product_id.with_context(warehouse=line.order_id.warehouse_id.id)
                product_qty = line.product_uom._compute_quantity(line.product_uom_qty, line.product_id.uom_id)
                if float_compare(product.virtual_available, product_qty, precision_digits=precision) == -1:
                    is_available = line._check_routing()

                    if not is_available:

                        ticket = self.env['helpdesk.ticket'].search([('product_id', '=', line.product_id.id), ('create_date', '>', (datetime.today() - relativedelta.relativedelta(days=day)).strftime('%Y-%m-%d 00:00:00')), ('stage_id.is_close', '=', False)])
                        if not ticket or ticket.stage_id.is_close:
                            vals = {'name': 'Inventory Warning: ' + line.product_id.name,
                                    'team_id': team.id,
                                    # 'user_id': 1,
                                    # 'ticket_type_id':,
                                    'product_id': line.product_id.id,
                                    'description': 'Low level inventory for ' + line.product_id.name,
                                    }
                            ticket = self.env['helpdesk.ticket'].create(vals)
                        msg = 'Order %s contain %s %s of %s. ' %(line.order_id.name, line.product_uom_qty, line.product_uom.name, line.product_id.name)
                        ticket.message_post(body=msg)
        return res



SaleOrderLine()
