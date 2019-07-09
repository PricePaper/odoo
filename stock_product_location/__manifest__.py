# -*- coding: utf-8 -*-

{
    'name': 'Stock Product Location',
    'version': '0.1',
    'category': 'Warehouse Management',
    'description': """
           This module defines a default stock location for products and product groups.
           This will be used 
           * as destination location for purchases and production
           * as source location for sales and internal moves

           """,
    'author': 'Confianz Global',
    'website': 'http://www.confianzit.com',
    'depends': ['product', 'stock', 'sale', 'purchase'],
    'data': ['security/ir.model.access.csv',
             'views/product_view.xml',
             'views/stock_move_by_location_view.xml',
                   ],
    
    'installable' : True,
    'active'      : False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
