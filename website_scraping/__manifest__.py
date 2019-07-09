# -*- coding: utf-8 -*-

{
    'name': 'Fetching Competitor Price',
    'version': '1.0',
    'category': 'Sales and Purchase',
    'summary': "Sales and Purchase",
    'description': """
Custom module implemented for fetching Competitor price.
       """,
    'author': 'Confianz Global',
    'website': 'http://confianzit.com',
    'images': [],

    'data': [
             'security/security.xml',
             'security/ir.model.access.csv',
             'views/product_sku_ref.xml',
             'views/website_scrap_config.xml',
             'views/competitor_website_price.xml',
             'views/price_fetch_schedule_view.xml',
             'views/product_pricelist.xml',
             'views/menu.xml',
             'data/data.xml',
            ],

    'depends': ['price_paper'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
