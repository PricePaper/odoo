# -*- coding: utf-8 -*-


{
    'name' : 'Deviated Cost Sale Report',
    'version' : '1.0',
    'summary': 'Deviated Cost Sale Report',
    'description': """
Deviated Cost Sale Report
=================================
    """,
    'author': 'Confianz Global',
    'website': 'http://confianzit.com',

    'data': [
             'views/price_paper_report.xml',
             'views/deviated_cost_report.xml',
             'views/sale_order.xml',
             'wizard/deviated_cost_sales.xml',
             'views/res_category_product_price.xml',
             'wizard/upload_product_cost.xml',
             'views/deviated_cost_contract.xml',
             'views/res_partner.xml',
             'views/menu.xml',
             'security/ir.model.access.csv',
            ],

    'depends' : ['sale_management','account','price_paper'],
    'installable': True,
    'application': False,
    'auto_install': False,

}
















# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
