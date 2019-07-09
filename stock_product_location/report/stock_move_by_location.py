##############################################
#
# ChriCar Beteiligungs- und Beratungs- GmbH
# Copyright (C) ChriCar Beteiligungs- und Beratungs- GmbH
# all rights reserved
# created 2009-09-19 23:51:03+02
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs.
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company.
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU Affero General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/> or
# write to the Free Software Foundation, Inc.,
# 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
###############################################
from odoo import api, fields, models, _


class StockMoveLocation(models.Model):
    _name = "stock.move.by.location"
    _description = "Location Moves"
    _auto = False

    id = fields.Char(string='id', readonly=True)
    description = fields.Char(string ='Description', readonly=True)
    location_id = fields.Many2one('stock.location', string='Location', readonly=True)
    product_id = fields.Many2one('product.product', string='Product',  readonly=True)
    categ_id = fields.Many2one(related='product_id.categ_id', relation="product.category", string='Category', readonly=True)
    name = fields.Float(string='Quantity', digits=(16, 2), readonly=True)
    uom_id = fields.Many2one(related='product_id.uom_id', relation="product.uom", string="UoM", readonly=True)
    product_qty_pending = fields.Float(string='Quantity Pending', digits=(16, 2), readonly=True)
    date = fields.Datetime(string='Date Planned',  readonly=True)
    picking_id = fields.Many2one('stock.picking', string='Packing',  readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True)
    
    def init(self):
        self.env.cr.execute("""create or replace view stock_move_by_location
as
select i.id ,
 l.id as location_id,product_id,
 i.name as description,
 case when state ='done' then product_qty else 0 end as name,
 case when state !='done' then product_qty else 0 end as product_qty_pending,
 date,
 picking_id,l.company_id
from stock_location l,
     stock_move i
where l.usage='internal'
  and i.location_dest_id = l.id
  and state != 'cancel'
  and i.company_id = l.company_id
union all
select -o.id ,
l.id as location_id ,product_id,
 o.name as description,
 case when state ='done' then -product_qty else 0 end as name,
 case when state !='done' then -product_qty else 0 end as product_qty_pending,
 date, 
 picking_id,l.company_id
from stock_location l,
     stock_move o
where l.usage='internal'
  and o.location_id = l.id
  and state != 'cancel'
  and o.company_id = l.company_id
;""")


StockMoveLocation()
