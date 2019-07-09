# -*- coding: utf-8 -*-

{
    'name': 'Global Price Change',
    'version': '1.0',
    'category': 'Product Pricing',
    'summary': "Inventory",
    'description': """
Custom module implemented for Global price change
       """,
    'author': 'Confianz Global',
    'website': 'http://confianzit.com',
    'images': [],

    'data': [
            'security/ir.model.access.csv',
            'data/data.xml',
            'views/global_price_change.xml',
            ],

    'depends': ['price_paper'],
    'installable': True,
    'auto_install': False,
    'application': False,
}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
