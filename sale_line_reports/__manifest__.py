# -*- coding: utf-8 -*-

{
    'name': 'Sale Line Reports',
    'version': '1.0',
    'category': 'Sales and Purchase',
    'summary': "Sales and Purchase",
    'description': """
Sale Line Reports module implemented for Price Papers.
=================================================================
Sale Line Reports module implemented for Price Papers.
       """,
    'author': 'Confianz Global',
    'website': 'http://confianzit.com',
    'images': [],

    'data': [
             'views/sale_order_line.xml',
             'views/product_category_view.xml',
#             'views/res_company_view.xml',
            ],

    'depends': ['price_paper'],
    'installable': True,
    'auto_install': False,
    'application': False,
}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
