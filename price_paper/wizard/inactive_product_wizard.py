# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import UserError


class inactive_product_wizard(models.TransientModel):

    _name = 'inactive.product.report.wizard'

    latest_sale_date = fields.Date(string='Latest Sale Before')

    @api.multi
    def display_inactive_product_report(self):


        latest_sale_date = "%s 00:00:00" %(str(self.latest_sale_date))

        self._cr.execute("select product.id from product_product product join product_template template ON (product.product_tmpl_id = template.id) where product.id not in (select sol.product_id from sale_order_line sol join sale_order so ON (so.id = sol.order_id) where so.confirmation_date > '%s' and so.state in ('sale', 'done')) and template.type != 'service' and template.sale_ok='t' and product.active='t'" %(latest_sale_date))

        pro_ids = self._cr.fetchall()
        product_ids = [pro_id and pro_id[0] for pro_id in pro_ids]


        action_id = self.env.ref('product.product_normal_action_sell').read()[0]
        if action_id:
            return {
                'name':  _('Inactive Products Since %s' %(self.latest_sale_date)),
                'type': action_id['type'],
                'res_model': action_id['res_model'],
                'view_type': action_id['view_type'],
                'view_mode': 'tree,form',
                'search_view_id': action_id['search_view_id'],
                'domain': [["id", "in", product_ids]],
                'help': action_id['help'],
            }





inactive_product_wizard()
