# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

class HelpDeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    is_special_order_ticket = fields.Boolean(string='Special Order Ticket', related='team_id.is_special_order_team')
    product_name = fields.Char(string='Product name')
    manufacturer = fields.Char(string='Manufacturer')
    item_description = fields.Text(string='Item Description')
    standard_price = fields.Float(string='Desired Selling Price')
    lead_time = fields.Integer(string='Desired lead time')
    have_picture = fields.Boolean(string='Do you have a picture?')
    upload_file = fields.Binary(string='File', help="Upload picture here")
    file_name = fields.Char(string='File name')
    is_pricing_request = fields.Boolean(string='Is this a request for pricing only?')
    is_one_time = fields.Boolean(string='Is this a one time purchase?')
    usage_per_month = fields.Char(string='Usage per month?')


    stage_code = fields.Selection([('special_item_requests_stage_new', 'New Special Requests'),
                                   ('special_item_requests_stage_greg', 'Assign to Greg'),
                                   ('special_item_requests_stage_available', 'Available'),
                                   ('special_item_requests_stage_suggest', 'Suggest Equivalent'),
                                   ('special_item_requests_stage_special', 'Request to Purchase'),
                                   ('special_item_requests_stage_accept_suggested', 'Accepted Suggested Available'),
                                   ('special_item_requests_stage_accept_alternative', 'Accepted Suggested Alternative'),
                                   ('special_item_requests_stage_reject', 'Move Forward With Special item Request'),
                                   ('special_item_requests_stage_close', 'Closed'),
                                  ], compute='_compute_stage_code', string='Stage Code')
    item_line_ids = fields.One2many('items.available', 'ticket_id', string='Available/Suggested Items')
    response = fields.Selection([('available', 'Available in Stock'), ('suggest', 'Suggested Alternative'), ('special', 'Special Request to Purchasing')])

    @api.multi
    def _compute_stage_code(self):
        for ticket in self:
            if not ticket.is_special_order_ticket:
                continue
            stage_ext_id = self.stage_id.get_external_id()
            if stage_ext_id:
                ticket.stage_code = stage_ext_id.get(ticket.stage_id.id, False) and stage_ext_id.get(ticket.stage_id.id, False).split('.')[1]




    @api.multi
    def assign_to_greg(self):
        stage_id = self.env.ref('special_item_requests.special_item_requests_stage_greg')
        user_greg = self.env['res.users'].search([('login', '=', 'greg@pricepaper.com')])
        for ticket in self:
            ticket.user_id = user_greg and user_greg.id
            ticket.stage_id = stage_id.id

    @api.multi
    def mark_as_available(self):
        stage_id = self.env.ref('special_item_requests.special_item_requests_stage_available')
        for ticket in self:
            if not ticket.item_line_ids:
                raise ValidationError('Please specify available items information under Availble/Suggested Item tab')
            ticket.response = 'available'
            ticket.stage_id = stage_id.id
            ticket.user_id = ticket.create_uid and ticket.create_uid.id

    @api.multi
    def suggest_equivalent(self):
        stage_id = self.env.ref('special_item_requests.special_item_requests_stage_suggest')
        for ticket in self:
            if not ticket.item_line_ids:
                raise ValidationError('Please suggests items under Availble/Suggested Item tab')
            ticket.response = 'suggest'
            ticket.stage_id = stage_id.id
            ticket.user_id = ticket.create_uid and ticket.create_uid.id

    @api.multi
    def special_request_to_purchasing(self):
        stage_id = self.env.ref('special_item_requests.special_item_requests_stage_special')
        user_angela = self.env['res.users'].search([('login', '=', 'angela@pricepaper.com')])
        for ticket in self:
            ticket.response = 'special'
            ticket.user_id = user_angela and user_angela.id
            ticket.stage_id = stage_id.id

    @api.multi
    def accept_suggested_available(self):
        stage_id = self.env.ref('special_item_requests.special_item_requests_stage_accept_suggested')
        for ticket in self:
            ticket.stage_id = stage_id.id

    @api.multi
    def accept_suggested_alternative(self):
        stage_id = self.env.ref('special_item_requests.special_item_requests_stage_accept_alternative')
        for ticket in self:
            ticket.stage_id = stage_id.id


    @api.multi
    def reject_suggestion(self):
        stage_id = self.env.ref('special_item_requests.special_item_requests_stage_reject')
        for ticket in self:
            ticket.stage_id = stage_id.id

    @api.multi
    def close_special_order_ticket(self):
        stage_id = self.env.ref('special_item_requests.special_item_requests_stage_close')
        for ticket in self:
            ticket.stage_id = stage_id.id




#    @api.model
#    def default_get(self, fields):
#        res = super(HelpDeskTicket, self).default_get(fields)
#        if res.get('team_id'):
#            team = self.env['helpdesk.team'].browse(res.get('team_id'))
#            team_ext_id = team.get_external_id()
#            if team_ext_id:
#                team_ext_id = team_ext_id.get(team.id, False) and team_ext_id.get(team.id, False).split('.')[1]
#                if team_ext_id == 'special_item_requests_team':
#                    ticket_type = self.env.ref('special_item_requests.special_item_requests_ticket_type')
#                    res['ticket_type_id'] = ticket_type.id
#        return res






HelpDeskTicket()



class ItemsAvailable(models.Model):
    _name = 'items.available'

    ticket_id = fields.Many2one('helpdesk.ticket', string='Ticket')
    product_id = fields.Many2one('product.product', string='Product')
    description = fields.Text(string='Description')


ItemsAvailable()








class HelpDeskTeam(models.Model):
    _inherit = 'helpdesk.team'

    is_special_order_team = fields.Boolean(string='Special Order Processing Team')

HelpDeskTeam()


