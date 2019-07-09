# -*- coding: utf-8 -*-

{
    'name': 'Special Item Requests',
    'version': '1.0',
    'category': 'Others',
    'summary': "Others",
    'description': """
Custom module implemented for Price Papers for creating Special Item Requests.
==================================================================================
Users can create a helpdesk ticket specifically for special orders.
       """,
    'author': 'Confianz Global',
    'website': 'http://confianzit.com',
    'images': [],

    'data': [
                'data/data.xml',
                'views/helpdesk_view.xml',
                'security/ir.model.access.csv',
             ],

    'depends': ['helpdesk'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
