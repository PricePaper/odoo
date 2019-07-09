# -*- coding: utf-8 -*-

{
    'name': 'Purchase Extension',
    'version': '1.0',
    'category': 'Purchase',
    'summary': "Purchase",
    'description': """
Custom module implemented for Purchase extension.
       """,
    'author': 'Confianz Global',
    'website': 'http://confianzit.com',
    'images': [],

    'data': [
            'wizard/view_sale_history_po_views.xml',
            'wizard/discount_check_generate.xml',
            'wizard/update_vendor_pricelist_view.xml',
            'wizard/add_sales_history_to_po.xml',
            'views/res_company.xml',
            'views/account_vendor_bill.xml',
            'views/payment_term.xml',
            'views/purchase_order.xml',
            'views/res_partner.xml',
            'views/sale_order.xml',
            'views/product_view.xml',
            ],

    'depends': ['purchase', 'price_paper'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
