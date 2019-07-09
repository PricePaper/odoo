# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import models, fields, api


class Lead(models.Model):

    _inherit = "crm.lead"


    rev_per_trans = fields.Float(string="Revenue Per Transaction")
    business_freq = fields.Selection(selection=[('week', 'Weekly'),
                                                ('biweek', 'Biweekly'),
                                                ('month', 'Monthly')], string="Frequency")
    planned_revenue = fields.Float(compute="_calc_expected_revenue", string='Monthly Revenue Expected', store=True)



    @api.depends('rev_per_trans', 'business_freq')
    def _calc_expected_revenue(self):
        """
        calculates the expected revenue
        multiplies frequency and revenue
        per transaction
        """
        for lead in self:
            if lead.rev_per_trans and lead.business_freq:
                if lead.business_freq == 'week':
                    lead.planned_revenue = lead.rev_per_trans*4
                elif lead.business_freq == 'biweek':
                    lead.planned_revenue = lead.rev_per_trans*2
                elif lead.business_freq == 'month':
                    lead.planned_revenue = lead.rev_per_trans



    def write(self, vals):
        """
        if the lead has got business_freq
        and revenue/transaction info associated with them,
        then copy it down to the partner when the lead is
        associated with one
        """
        res = super(Lead, self).write(vals)
        for lead in self:
            if vals.get('partner_id', False):
                partner = self.env['res.partner'].browse(vals.get('partner_id'))
                partner.rev_per_trans = lead.rev_per_trans or vals.get('rev_per_trans', 0.00)
                partner.business_freq = lead.business_freq or vals.get('business_freq', '')


Lead()
