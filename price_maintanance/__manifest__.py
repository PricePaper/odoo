# -*- coding: utf-8 -*-

{
    'name': 'Price Maintanace',
    'version': '1.0',
    'category': 'Sales and Purchase',
    'summary': "Sales and Purchase",
    'description': """
Custom module implemented for Price maintanance.
       """,
    'author': 'Confianz Global',
    'website': 'http://confianzit.com',
    'images': [],

    'data': [
            'security/ir.model.access.csv',
            'data/data.xml',
            'wizard/price_edit_note.xml',
            'views/price_edit_notes.xml',
            'views/res_company.xml',
            'views/product.xml',
            'views/customer.xml',
            ],

    'depends': ['website_scraping', 'crm_enhancements', 'base_address_city'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
