# -*- coding: utf-8 -*-

from odoo import api, models


class ReportBatchProductLabel(models.AbstractModel):

    _name = "report.batch_delivery.report_batch_product_label"

    def _get_product_labels(self, docs):
        picking_ids = self.env['stock.picking']
        for doc in docs:
            picking_ids += doc.picking_ids
        ordered_product_label = self.get_ordered_product_label(picking_ids)
        return ordered_product_label

    def get_ordered_product_label(self, pickings):
        location_main = {}
        for picking in pickings:
            for line in picking.move_lines:
                location = line.product_id.property_stock_location and line.product_id.property_stock_location.name or '00-Location not assigned'
                if location_main.get(location, False):
                    location_main.get(location, False).append(line)
                else:
                    location_main.update({location: [line]})
        locations = location_main.keys()
        location_list = []
        for location in sorted(locations):
            location_list.append((location, location_main[location]))
        return location_list


    @api.model
    def get_report_values(self, docids, data=None):
        docs = self.env['stock.picking.batch'].browse(docids)
        return {'doc_ids': docs.ids,
                'doc_model': 'stock.picking.batch',
                'docs': docs,
                'data': data,
                'get_product_labels': self._get_product_labels,
            }


class ReportpickingProductLabel(models.AbstractModel):

    _name = "report.batch_delivery.report_product_label"

    def _get_product_labels(self, docs):
        picking_ids = self.env['stock.picking']
        for doc in docs:
            picking_ids += doc
        ordered_product_label = self.env['report.batch_delivery.report_batch_product_label'].get_ordered_product_label(picking_ids)
        return ordered_product_label

    @api.model
    def get_report_values(self, docids, data=None):
        docs = self.env['stock.picking'].browse(docids)
        return {'doc_ids': docs.ids,
                'doc_model': 'stock.picking',
                'docs': docs,
                'data': data,
                'get_product_labels': self._get_product_labels,
            }


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
