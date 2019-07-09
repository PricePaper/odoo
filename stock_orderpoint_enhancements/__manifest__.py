# -*- coding: utf-8 -*-
{
    'name': "Stock Orderpoint Enhancements",

    'summary': """
        Implements custom logic for orderpoints minimum and maximum quantity computation based on previous order histories
    """,

    'description': """
        Implements custom logic for orderpoints minimum and maximum quantity computation based on previous order histories.
        This can work as a forecast for inventory.
    """,

    'author': 'Confianz Global',
    'website': 'http://confianzit.com',


    'category': 'Inventory',
    'version': '0.1',


    'depends': ['stock','odoo_fbprophet', 'price_paper', 'queue_job'],


    'data': [
#        'security/ir.model.access.csv',
        'data/data.xml',
        'wizard/product_forecast_views.xml',
        'views/res_company.xml',
        'views/product.xml',
        'views/partner.xml',
        'views/fbprophet_config_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,

}
