# -*- coding: utf-8 -*-

{
    'name': 'Price Paper Batch Delivery',
    'version': '1.0',
    'category': 'Delivery',
    'summary': "Sales and Purchase",
    'description': """
Custom module implemented for Price Papers Batch Delivery Process.
=====================================================================
This module sets up the batch delivery process for price paper.
       """,
    'author': 'Confianz Global',
    'website': 'http://confianzit.com',
    'images': [],

    'data': [
             'data/data.xml',
             'wizard/assign_route_wizard_view.xml',
#             'wizard/driver_invoice_wizard_view.xml',
             'views/truck_route_view.xml',
             'views/truck_driver_view.xml',
             'views/batch_delivery_view.xml',
             'views/stock_picking_view.xml',
             'views/stock_location_view.xml',
             'views/partner_view.xml',
             'views/report_product_label.xml',
             'views/report_batch_driver.xml',
             'views/report_batch_delivery_slip.xml',
             'views/report_master_pick_ticket.xml',
             'views/report_stockpicking_operations.xml',
             'views/report_template.xml',
#             'views/product_view.xml',
             'views/account_view.xml',
             'views/sale_view.xml',
             'views/website_asset.xml',
             'security/ir.model.access.csv',
            ],

    'depends': ['price_paper', 'stock_picking_batch', 'base_geolocalize','website_google_map','website_customer', 'account_reports', 'stock_product_location'],
    'installable': True,
    'auto_install': False,
    'application': False,
}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
