# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import ValidationError
import csv
import io
import base64

class UploadFileWizard(models.TransientModel):

    _name = "upload.csv.file.wizard"
    _description = "Upload Vendor Product Price"

    upload_file = fields.Binary(string='File', help="File to check and/or import, raw binary (not base64)")
    file_name = fields.Char(string='File name')
    product_ids = fields.Many2many('res.category.product.cost', 'product_id', string="Products" )


    @api.multi
    @api.onchange('upload_file')
    def onchange_load_data(self):
        """
        When a new csv file is uploaded, this method checks
        the file type, and integrity and loads product data
        in the file into the product_ids. if no file, it resets 
        the lines.
        """
        for data in self:
            if not data.upload_file:
                data.product_ids = []
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
                if count == 0:
                    count += 1
                    if  (row[0].lower().strip() not in ('vendor_product_code','vendor product code') or row[1].lower().strip() not in ('cost')):
                        data.upload_file = ''
                        data.file_name = ''
                        return {'warning': {'title': 'Error!', 'message': 'Incompatiable csv file!\nThe column headers should be \'Vendor Product Code,Cost\' and should also follow the same order.'}}

                else:
                    product = self.env['product.supplierinfo'].search([('product_code', '=ilike', row[0].strip())])
                    if product and not(len(product) > 1):
                        product_id = product.product_id or product.product_tmpl_id.id
                        cost =  float(row[1].strip() or 0.0)
                    else:
                        if not product:
                            message = 'No Product found for Vendor Product Code %s' % row[0].strip()
                        else:
                            message = 'Multiple Product found for Vendor Product Code %s' % row[0].strip()
                        return {'warning': {'title': 'Error!', 'message': message}}
                        break
                    result.append({'product_id': product_id,
                                   'cost': cost,
                                  })
            data.product_ids = result



    @api.multi
    def import_products(self):
        """
        Update product and cost of  contract with data
        uploaded through csv
        """
        self.ensure_one()
        contract_id = self.env['deviated.cost.contract'].browse(self.env.context.get('contract_id', False))
        lines = []
        if contract_id:
            for line in self.product_ids:
                vals = {}
                vals.update({'product_id': line.product_id and line.product_id.id, 'cost': line.cost})
                lines.append((0, False, vals))
            contract_id.write({'partner_product_ids' : lines})
        return True


UploadFileWizard()
