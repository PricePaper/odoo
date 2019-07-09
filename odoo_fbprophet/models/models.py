# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime
import calendar

try:
    import pandas as pd
#    import numpy as np
    from fbprophet import Prophet
    from pandas.tseries.holiday import USFederalHolidayCalendar
except ImportError:
    pass


class YearlyHolidays(models.Model):

    _name = 'yearly.holidays'
    _order = 'name'

    name = fields.Char(string='Year', required=True)
    days = fields.One2many('holiday.day', 'year_id', string='Days')

    @api.multi
    def get_holidays(self):
        """
        Get all US federal holidays
        in the given year
        """
        self.ensure_one()
        cal = USFederalHolidayCalendar()
        start = "%s-01-01" %(self.name)
        end = "%s-12-31" %(self.name)
        holidays = cal.holidays(start=start, end=end).to_pydatetime()
        holidays = [t.strftime('%Y-%m-%d')for t in holidays]
        existing_holidays = self.env['holiday.day'].search([('year_id', '=', self.id)])
        existing_holidays = [h.date for h in existing_holidays]
        for holiday in holidays:
            if holiday in existing_holidays:
                continue
            self.env['holiday.day'].create({'date': holiday, 'year_id':self.id})


    @api.constrains('name')
    def check_year(self):
        if not self.name.isdigit() or not len (self.name)==4 or int(self.name)>2260 or int(self.name)<1984:
            raise ValidationError(_('Please enter a valid year in four digits.'))
        if self.search([('name', '=', self.name), ('id', '!=', self.id)]):
            raise ValidationError(_('The year %s already exists in the system.' %(self.name)))

YearlyHolidays()

class Holiday(models.Model):

    _name = 'holiday.day'
    _order = 'date'

    date = fields.Date(string='Date')
    description = fields.Char(string="Description")
    day = fields.Char(string='Day', compute='_get_day')
    year_id = fields.Many2one('yearly.holidays', string='Year', ondelete='cascade')


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
    def check_year(self):
        if self.date and self.date.split('-')[0] != self.year_id.name:
            raise ValidationError(_('Holiday %s does not belong to this year.' %(self.date)))



Holiday()


class ProphetBridge(models.AbstractModel):

    _name = 'odoo_fbprophet.prophet.bridge'


    @api.model
    def remove_weekends_from_dataframe(self, dataframe):
        """
        removes the weekend days from the provided dataset
        """
        del_list = []
        for index, row in dataframe.iterrows():
            date = datetime.strptime(str(row['ds']), '%Y-%m-%d %H:%M:%S').date()
            if date.weekday() in (5, 6):
                del_list.append(index)
        dataframe.drop(dataframe.index[del_list], inplace=True)
        return dataframe



    @api.model
    def create_prophet_object(self, date_from, date_to, config=False):
        holidays = self.get_holidays_list(date_from, date_to)     #get holidays in a format conditioned for prophet.

        kwargs = {}

        kwargs.update({'holidays': holidays})

        if config:
            if config.changepoints:
                changepoints = []
                for changepoint in config.changepoints:
                    changepoints.append(changepoint.date)
                kwargs.update({'changepoints': changepoints})

            config.growth and kwargs.update({'growth': config.growth})
            config.n_changepoints and kwargs.update({'n_changepoints': config.n_changepoints})

            ref = {'1': True, '0': False, 'auto':'auto'}
            config.yearly_seasonality and kwargs.update({'yearly_seasonality': ref.get(config.yearly_seasonality)})
            config.weekly_seasonality and kwargs.update({'weekly_seasonality': ref.get(config.weekly_seasonality)})
            config.daily_seasonality and kwargs.update({'daily_seasonality': ref.get(config.daily_seasonality)})


            config.seasonality_prior_scale and kwargs.update({'seasonality_prior_scale': config.seasonality_prior_scale})
            config.holidays_prior_scale and kwargs.update({'holidays_prior_scale': config.holidays_prior_scale})
            config.changepoint_prior_scale and kwargs.update({'changepoint_prior_scale': config.changepoint_prior_scale})
            config.mcmc_samples and kwargs.update({'mcmc_samples': config.mcmc_samples})
            config.interval_width and kwargs.update({'interval_width': config.interval_width})
            config.uncertainty_samples and kwargs.update({'uncertainty_samples': config.uncertainty_samples})


        prophet_obj = Prophet(**kwargs)   #add all variables and initialise object
        return prophet_obj




    @api.model
    def run_prophet(self, dataset, date_from, date_to, periods=12, freq='m', config=False):
        """
        the core method that calls the fbprophet forecasting
        date from and date to is used to denotet the holidays
        ranges to be considered. periods and frequency is used
        to set the no of periods and frequency for the forecast
        daily seasonality is a parameter used to tell prophet if
        daily seasonality should be considered instead of monthly
        or weekly
        """
        dataframe = pd.DataFrame(dataset, columns=['ds', 'y'])  #convert the dataset to a pandas dataframe object with fbprophet forced coloumn names df and y

        if config and config.growth == 'logistic': #cap and floor values needs to be set if growth is set as logistic
            dataframe['cap'] = config.dataframe_cap
            dataframe['floor'] = config.dataframe_floor

        m = self.create_prophet_object(date_from, date_to, config=config)
        m.fit(dataframe)       #pass historical dataframe
        future = m.make_future_dataframe(periods=periods, freq=freq)     #make future dataframe
        future = self.remove_weekends_from_dataframe(future)

        if config and config.growth == 'logistic':  #cap and floor values needs to be set if growth is set as logistic
            future['cap'] = config.dataframe_cap
            future['floor'] = config.dataframe_floor

        forecast = m.predict(future)                      #run prophet to predict future
        forecast['ds'] = pd.to_datetime(forecast['ds']).apply(lambda x: x.date().strftime('%Y-%m-%d'))
        forecast = list(forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].itertuples(index=False, name="None")) # convert the result back to list of tuples
        return forecast


    @api.model
    def get_holidays_list(self, date_from, date_to):
        """
        Get all the holidays between date_from and to_date
        create a dataframe with the given data
        """

        holidays = self.env['holiday.day'].search([('date','>=',date_from), ('date', '<=', date_to)])
        if not holidays:
            raise ValidationError(_('Empty holidays list received,Please enter holidays with the path Settings/Technical/Yearly Holidays/Year'))
        holidays = holidays and [h.date for h in holidays] or []
        holidays = pd.DataFrame({
          'holiday': 'Holiday',
          'ds': pd.to_datetime(holidays),
          'lower_window': 0,
          'upper_window': 1,
        })
        return holidays














