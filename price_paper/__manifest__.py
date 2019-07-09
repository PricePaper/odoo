# -*- coding: utf-8 -*-

{
    'name': 'Price Paper',
    'version': '1.0',
    'category': 'Sales and Purchase',
    'summary': "Sales and Purchase",
    'description': """
Custom module implemented for Price Papers.
=================================================================
Custom module implemented for Price Paper.
       """,
    'author': 'Confianz Global',
    'website': 'http://confianzit.com',
    'images': [],

    'data': [
             'security/price_paper_security.xml',
             'security/ir.model.access.csv',
             'data/data.xml',
             'wizard/upload_pricelist.xml',
             'wizard/inactive_product_report_wizard.xml',
             'wizard/inactive_customer_report_wizard.xml',
             'wizard/add_purchase_history_to_so.xml',
             'views/res_company.xml',
             'views/stock_move.xml',
             'views/product_notes.xml',
             'views/sale_order.xml',
             'views/res_partner.xml',
             'views/product.xml',
             'views/cost_change.xml',
             'views/product_pricelist.xml',
             'views/customer_product_price.xml',
             'views/account_view.xml',
             'views/delivery_carrier_view.xml',
             'views/helpdesk_team_view.xml',
             'views/menu.xml',
            ],

    'depends': ['sale_stock', 'product', 'stock_account', 'purchase', 'account','sales_team','delivery','helpdesk'],
    'installable': True,
    'auto_install': False,
    'application': False,
}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
