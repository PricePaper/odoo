# -*- coding: utf-8 -*-

from odoo import api, models


class ReportMasterPickingTicket(models.AbstractModel):

    _name = "report.batch_delivery.master_pick_ticket_report"

    def _get_master_tickets(self, docs):
        picking_ids = self.env['stock.picking']
        for doc in docs:
            picking_ids += doc.picking_ids
        product_main = {}
        for picking in picking_ids:
            for line in picking.move_lines:
                location = line.product_id.property_stock_location and line.product_id.property_stock_location.name or '00-Location not assigned'
                if product_main.get(location, False):
                    if product_main.get(location, False).get(line.product_id, False):
                        if line.product_uom in  product_main.get(location, False).get(line.product_id, False):
                            product_main.get(location, False).get(line.product_id, False)[line.product_uom] = product_main.get(location, False).get(line.product_id, False).get(line.product_uom, 0)+line.quantity_done
                        else:
                            product_main.get(location, False).get(line.product_id, False)[line.product_uom] = line.quantity_done
                    else:
                        product_main.update({location: {line.product_id:{line.product_uom:line.quantity_done}}})
                else:
                    product_main.update({location: {line.product_id:{line.product_uom:line.quantity_done}}})
        locations = product_main.keys()
        location_list = []
        for location in sorted(locations):
            location_list.append((location, product_main[location]))
        return location_list

    @api.model
    def get_report_values(self, docids, data=None):
        docs = self.env['stock.picking.batch'].browse(docids)
        return {'doc_ids': docs.ids,
                'doc_model': 'stock.picking.batch',
                'docs': docs,
                'data': data,
                'get_master_tickets': self._get_master_tickets,
            }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
