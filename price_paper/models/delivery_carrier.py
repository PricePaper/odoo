from odoo import models, fields, api, _

class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    average_company_cost = fields.Float(string='Average Company Cost', help='The Average amount that costs for the company to make this delivery.', default=80.00)

DeliveryCarrier()
