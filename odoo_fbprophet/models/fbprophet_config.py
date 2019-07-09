# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from datetime import datetime
import calendar
from odoo.exceptions import ValidationError



class FbprophetConfig(models.Model):
    _name = 'fbprophet.config'

    name = fields.Char(string='Name', required="True")

    config_type = fields.Selection([('default', 'Default')], string='Configuration For', default='default')

    growth = fields.Selection([('linear', 'Linear'), ('logistic', 'Logistic')], string='Growth', help="linear or logistic to specify a linear or logistic trend", default='linear')

    dataframe_cap = fields.Float(string='Saturating Maximum', help='Carrying capacity Cap value')

    dataframe_floor = fields.Float(string='Saturating Minimum', help='Carrying capacity Floor value')

    changepoints = fields.One2many('changepoint.dates', 'parent_id', string='Changepoint dates', help='List of dates at which to include potential changepoints. If not specified, potential changepoints are selected automatically.')

    n_changepoints = fields.Integer(string='Changepoint Number', default=25, help='Number of potential changepoints to include. Not used if input `changepoints` is supplied. If `changepoints` is not supplied, then n_changepoints potential changepoints are selected uniformly from the first 80 percent of the history.')

    yearly_seasonality = fields.Selection([('auto', 'Auto'), ('1', 'True'), ('0', 'False')], string="Yearly Seasonality", help="Fit yearly seasonality.", default="auto")

    weekly_seasonality = fields.Selection([('auto', 'Auto'), ('1', 'True'), ('0', 'False')], string="Weekly Seasonality", help="Fit weekly seasonality.", default="auto")

    daily_seasonality = fields.Selection([('auto', 'Auto'), ('1', 'True'), ('0', 'False')], string="Daily Seasonality", help="Fit daily seasonality.", default="1")

    seasonality_prior_scale = fields.Float(string="Seasonality Prior Scale", default=10.0, help="Parameter modulating the strength of the seasonality model. Larger values allow the model to fit larger seasonal fluctuations, smaller values dampen the seasonality.")

    holidays_prior_scale = fields.Float(string="Holidays Prior Scale", default=10.0, help="Parameter modulating the strength of the holiday components model, unless overridden in the holidays input.")

    changepoint_prior_scale = fields.Float(default=0.05, string='Changepoint Prior Scale', help="Parameter modulating the flexibility of the automatic changepoint selection. Large values will allow many changepoints, small values will allow few changepoints.")

    mcmc_samples = fields.Integer(default=0, help='if greater than 0, will do full Bayesian inference with the specified number of MCMC samples. If 0, will do MAP estimation.', string='MCMC Samples')

    interval_width = fields.Float(default=0.8, string='Interval Width', help='width of the uncertainty intervals provided for the forecast. If mcmc_samples=0, this will be only the uncertainty in the trend using the MAP estimate of the extrapolated generative model. If mcmc.samples>0, this will be integrated over all model parameters, which will include uncertainty in seasonality.')

    uncertainty_samples = fields.Integer(help='Number of simulated draws used to estimate uncertainty intervals.', string='Uncertainty Samples', default='1000')



    @api.constrains('dataframe_cap','growth')
    def change_dataframe_cap(self):
        """
        Saturating maximum must be >1 for growth 'logistic'
        """
        if self.growth == 'logistic' and self.dataframe_cap <= 1:
            raise ValidationError(_("Saturating Maximum should be greater than 1."))


    @api.constrains('interval_width')
    def change_interval_width(self):
        """
        Interval width must be in the range 0-1
        """
        if not (self.interval_width >= 0 and self.interval_width <=1 ):
            raise ValidationError(_("Interval width should be in the range 0.0-1.0"))



FbprophetConfig()


class ChangepointDates(models.Model):

    _name = 'changepoint.dates'
    _order = 'date'

    parent_id  = fields.Many2one('fbprophet.config', string='Configuration')
    date = fields.Date(string='Date', required=True)
    description = fields.Char(string="Description")
    day = fields.Char(string='Day', compute='_get_day')



    @api.depends('date')
    def _get_day(self):
        """
        Method to get the the
        name of week day
        """
        for date in self:
            if date.date:
                date_obj = datetime.strptime(date.date, '%Y-%m-%d').date()
                date.day = calendar.day_name[date_obj.weekday()]


    @api.constrains('date')
    def change_point_date(self):
        """
        date should be prior to today
        """
        date_order = datetime.strptime(self.date, '%Y-%m-%d')
        date_today = datetime.strptime(fields.Date.context_today(self), '%Y-%m-%d')
        if date_order >  date_today:
            raise ValidationError(_('Changepoint date should be prior to today.'))




ChangepointDates()
