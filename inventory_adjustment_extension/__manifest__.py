# -*- coding: utf-8 -*-

{
    'name': 'Price Paper Inventory Adjustment',
    'version': '1.0',
    'category': 'Inventory',
    'summary': "Inventory Adjustment",
    'description': """
Custom module implemented for Price Papers Inventory Adjustment.
=====================================================================
This module sets up the inventory Adjustment process for price paper.
       """,
    'author': 'Confianz Global',
    'website': 'http://confianzit.com',
    'images': [],

    'data': [
            'views/report_stock_inventory.xml',
            'views/stock_inventory.xml',
            ],

    'depends': ['stock','batch_delivery'],
    'installable': True,
    'auto_install': False,
    'application': False,
}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
