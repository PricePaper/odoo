from odoo import api, fields, models, _

class ProductionLot(models.Model):

    _inherit = "stock.production.lot"

    @api.one
    def _product_qty(self):
        """ This functional field method for product qty computation
            has to be redefined to exclude products in transit location.
        """
        # We only care for the quants in internal or transit locations.
        quants = self.quant_ids.filtered(lambda q: q.location_id.usage in ['internal', 'transit'] and q.location_id.is_transit_location == False)
        self.product_qty = sum(quants.mapped('quantity'))




ProductionLot()
