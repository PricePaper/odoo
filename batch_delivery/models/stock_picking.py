# -*- coding: utf-8 -*-

from odoo import models, fields, registry, api,_
from odoo.exceptions import UserError

class StockPicking(models.Model):

    _inherit = 'stock.picking'

    _order = 'release_date, deliver_by'

    truck_driver_id = fields.Many2one('res.partner', string='Truck Driver', copy=False)
    route_id = fields.Many2one('truck.route', string='Truck Route', group_expand='_read_group_route_ids', copy=False)
    is_delivered = fields.Boolean(string='Delivered', copy=False)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting Another Operation'),
        ('confirmed', 'Waiting'),
        ('assigned', 'Ready'),
        ('done', 'In Transit'),
        ('delivered', 'Delivered'),
        ('cancel', 'Cancelled'),
    ], string='Status', compute='_compute_state',
        copy=False, index=True, readonly=True, store=True, track_visibility='onchange',
        help=" * Draft: not confirmed yet and will not be scheduled until confirmed.\n"
             " * Waiting Another Operation: waiting for another move to proceed before it becomes automatically available (e.g. in Make-To-Order flows).\n"
             " * Waiting: if it is not ready to be sent because the required products could not be reserved.\n"
             " * Ready: products are reserved and ready to be sent. If the shipping policy is 'As soon as possible' this happens as soon as anything is reserved.\n"
             " * Done: has been processed, can't be modified or cancelled anymore.\n"
             " * Cancelled: has been cancelled, can't be confirmed anymore.")

    street = fields.Char(string='Street', related='partner_id.street')
    street2 = fields.Char(string='Street2', related='partner_id.street2')
    city = fields.Char(string='City', related='partner_id.city')
    state_id = fields.Many2one('res.country.state', string='State', related='partner_id.state_id')
    zip = fields.Char(string='Zip', related='partner_id.zip')
    delivery_notes = fields.Char(string='Delivery Notes', related='partner_id.delivery_notes')
    item_count = fields.Integer(string="Item Count", compute='_compute_item_count')
    partner_loc_url = fields.Char(string="Partner Location", related='partner_id.location_url')
    release_date = fields.Date(related='sale_id.release_date', string="Earliest Delivery Date", store=True)
    deliver_by = fields.Date(related='sale_id.deliver_by', string="Deliver By", store=True)
    delivery_move_ids = fields.One2many('stock.move', 'delivery_picking_id', string='Transit Moves')
    delivery_move_line_ids = fields.One2many('stock.move.line', 'delivery_picking_id', string='Transit Move Lines')
    shipping_easiness = fields.Selection(related='partner_id.shipping_easiness', string='Easiness Of Shipping')




    @api.multi
    def _compute_item_count(self):
        for picking in self:
            count=0
            for line in picking.move_lines:
                count += line.product_uom_qty
            picking.item_count = count




    @api.depends('move_type', 'is_delivered', 'move_lines.state', 'move_lines.picking_id')
    @api.one
    def _compute_state(self):
        ''' State of a picking depends on the state of its related stock.move
        - Draft: only used for "planned pickings"
        - Waiting: if the picking is not ready to be sent so if
          - (a) no quantity could be reserved at all or if
          - (b) some quantities could be reserved and the shipping policy is "deliver all at once"
        - Waiting another move: if the picking is waiting for another move
        - Ready: if the picking is ready to be sent so if:
          - (a) all quantities are reserved or if
          - (b) some quantities could be reserved and the shipping policy is "as soon as possible"
        - Done: if the picking is done.
        - Cancelled: if the picking is cancelled
        '''
        if not self.move_lines:
            self.state = 'draft'
        elif any(move.state == 'draft' for move in self.move_lines):  # TDE FIXME: should be all ?
            self.state = 'draft'
        elif all(move.state == 'cancel' for move in self.move_lines):
            self.state = 'cancel'
        elif self.is_delivered:
            self.state = 'delivered'
        elif all(move.state in ['cancel', 'done'] for move in self.move_lines):
            self.state = 'done'
        else:
            relevant_move_state = self.move_lines._get_relevant_state_among_moves()
            if relevant_move_state == 'partially_available':
                self.state = 'assigned'
            else:
                self.state = relevant_move_state



    @api.model
    def _read_group_route_ids(self, routes, domain, order):
        route_ids = self.env['truck.route'].search([('set_active', '=', True)])
        return route_ids

    @api.multi
    def write(self, vals):

        for picking in self:



#            in_transit = vals.get('in_transit', False)
#            if in_transit:
#                historical_picking = self.env['stock.picking'].search([('route_id', '!=', False), ('state', '=', 'done'), ('picking_type_id.code', '=', 'outgoing'), ('partner_id', '=', picking.partner_id.id)], order='create_date desc', limit=1)

#                route_id = historical_picking and historical_picking.route_id and historical_picking.route_id.id or False
#                if route_id:
#                    vals.update({'route_id': route_id})



            route_id = vals.get('route_id', False)
            if route_id:
                draft_batch = self.env['stock.picking.batch'].search([('state', '=', 'draft'), ('route_id', '=', route_id)], limit=1)
                if not draft_batch:
                    draft_batch = self.env['stock.picking.batch'].create({'route_id': route_id})
                if picking.state not in ('assigned', 'done'):
                    error = "The requested operation cannot be processed because all quantities are not available for picking %s. Please assign quantities for this picking." %(picking.name)
                    raise UserError(_(error))
                picking.batch_id = draft_batch.id
            if 'route_id' in vals.keys() and not (vals.get('route_id', False)) and picking.batch_id and picking.batch_id.state == 'draft':
                vals.update({'batch_id': False})
        res = super(StockPicking, self).write(vals)
        return res



    @api.multi
    def action_done(self):
        res = super(StockPicking, self).action_done()
        for pick in self:
            if pick.picking_type_id.code in ('incoming', 'internal') and pick.state == 'done':
                pick.state ='delivered'
        return res





    @api.multi
    def deliver_products(self):
        transit_location = self.env['stock.location'].search([('is_transit_location', '=', True)], limit=1)
        customer_location = self.env['stock.location'].search([('usage', '=', 'customer')], limit=1)
        if not transit_location:
            raise UserError(_("Please go to stock locations and select a stock transit location by checking the field with string Truck Transit Location."))
        for picking in self:
            for move in picking.move_lines:
                move_lines = []
                for ml in move.move_line_ids:
                    move_lines.append({
                                                            'product_id': ml.product_id.id,
                                                            'product_uom_id': ml.product_uom_id.id,
                                                            'location_id': transit_location.id,
                                                            'location_dest_id': customer_location.id,
                                                            'qty_done': ml.qty_done,
                                                            'product_uom_qty': ml.product_uom_qty,
                                                            'lot_id': ml.lot_id.id,
                                                            'delivery_move_line_id': ml.id,
                                                            'picking_id': False,
                                                        })
                delivery_move = self.env['stock.move'].create({
                                                   'name': "%s Delivery Move: %s" %(picking.name, move.product_id.display_name),
                                                   'product_id': move.product_id.id,
                                                   'product_uom': move.product_uom.id,
                                                   'location_id': transit_location.id,
                                                   'location_dest_id': customer_location.id,
                                                   'state': 'draft',
                                                   'product_uom_qty': move.quantity_done,
                                                   'move_line_ids':[(0, 0, vals) for vals in move_lines],
                                                   'delivery_move_id': move.id,
                                                   'picking_id': False,
                                                   })
                delivery_move._action_confirm()
                delivery_move._action_assign()
                delivery_move._action_done()
            picking.is_delivered = True


    @api.multi
    def button_validate(self):
        """
        if there are movelines with reserved quantities
        and not validated, automatically validate them.
        """
        self.ensure_one()

        if self.picking_type_id.code == 'outgoing':
            for line in self.move_line_ids:
                if line.lot_id and line.pref_lot_id and line.lot_id != line.pref_lot_id:
                    raise UserError(_("This Delivery for product %s is supposed to use products from the lot %s please clear the Preferred Lot field to override" %(line.product_id.name, line.pref_lot_id.name)))

            no_quantities_done_lines = self.move_line_ids.filtered(lambda l: l.qty_done == 0.0)
            for line in no_quantities_done_lines:
                if line.move_id and line.move_id.product_uom_qty == line.move_id.reserved_availability:
                    line.qty_done = line.product_uom_qty

        res = super(StockPicking, self).button_validate()
        return res



StockPicking()
