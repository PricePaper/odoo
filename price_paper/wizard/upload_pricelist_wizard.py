# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import ValidationError
import csv
import io
import base64

class UploadFileWizard(models.TransientModel):

    _name = "upload.pricelist.csv.wizard"
    _description = "Upload Customer Pricelist"

    upload_file = fields.Binary(string='File', help="File to check and/or import, raw binary (not base64)")
    file_name = fields.Char(string='File name')
    customer_product_ids = fields.Many2many('customer.product.price', string="Customer Product Price" )


    @api.multi
    @api.onchange('upload_file')
    def onchange_load_data(self):
        """
        When a new csv file is uploaded, this method checks
        the file type, and integrity and loads pricelist data
        in the file into the customer_product_ids. if no file, it resets
        the lines.
        """
        for data in self:
            if not data.upload_file:
                data.customer_product_ids = []
                continue
            # check if valid csv file
            upld_file = base64.b64decode(data.upload_file).decode('utf-8')
            file_stream = io.StringIO(upld_file)
            if not data.file_name.endswith('.csv'):
                data.upload_file=''
                data.file_name=''
                return {'warning': {'title': 'Error!', 'message': 'Invalid File Type, Please import a csv file.'}}
            reader = csv.reader(file_stream, delimiter=',')
            count = 0
            result = []
            for row in reader:
                # check file integrity in first iteration
                msg =""
                if count == 0:
                    count += 1
                    if  self._context.get('is_competitor', False) == 'competitor' and (row[0].lower().strip() not in ('product_ref','product ref')  or  row[1].lower().strip() not in ('price')):
                        msg = 'Incompatiable csv file!\nThe column headers should be \Product ref,Price\' and should also follow the same order.'
                    else:
                       if  self._context.get('is_competitor', False) != 'competitor' and (row[0].lower().strip() not in ('product_ref','product ref')  or row[1].lower().strip() not in ('customer_code','customer code') or row[2].lower().strip() not in ('price')):
                            msg = 'Incompatiable csv file!\nThe column headers should be \Product ref,Customer code,Price\' and should also follow the same order.'
                    if msg:
                        data.upload_file = ''
                        data.file_name = ''
                        return {'warning': {'title': 'Error!', 'message': msg}}
                else:
                    product = self.env['product.product'].search([('default_code', '=ilike', row[0].strip())], limit=1)
                    product_id = product and product.id
                    if not product:
                        return {'warning': {'title': 'Error!', 'message': 'No Product found for Internal Reference %s' % row[0].strip()}}
                        break
                    val = {'product_id': product_id}
                    if self._context.get('is_competitor', False) != 'competitor':
                        customer = self.env['res.partner'].search([('customer_code', 'ilike', row[1].strip())], limit=1)
                        if not customer:
                            return {'warning': {'title': 'Error!', 'message': 'No Customer found for Customer Code %s' % row[1].strip()}}
                            break
                        val.update({'partner_id' : customer.id, 'price' : row[2].strip() or 0.0 })
                    else:
                        val.update({'price': row[1].strip() or 0.0})
                    result.append(val)
            data.customer_product_ids = result



    @api.multi
    def import_pricelists(self):
        """
        Update customer product price with the  data
        uploaded through csv
        """
        self.ensure_one()
        pricelist_id = self.env['product.pricelist'].browse(self._context.get('pricelist_id', False))
        lines = []
        if pricelist_id:
            for line in self.customer_product_ids:
                vals = { 'product_id':line.product_id.id, 'price': line.price}
                if pricelist_id.type != 'competitor':
                    vals.update({'partner_id': line.partner_id.id})
                lines.append((0, False, vals))
            pricelist_id.write({'customer_product_price_ids' : lines})
        return True


UploadFileWizard()
