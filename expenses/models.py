from django.db import models
from django.urls import reverse
from datetime import datetime as dt

from .storage import OverwriteStorage
import pandas as pd
# Create your models here.

col_rn = {'Datum': 'date', 'Naam / Omschrijving': 'name', 
          'Af Bij': 'af_bij', 'Bedrag (EUR)': 'amount'
         }
ing_cols = ['date', 'name', 'amount', 'category', 'description'] #, 'af_bij'



class expense_category(models.Model):
    name = models.TextField(max_length = 1000, help_text = 'expense category')
    frequency = models.IntegerField(unique = True, blank = True, null = True)
    
    class Meta:
        ordering = ['frequency']
        verbose_name = "Expense Category"
        verbose_name_plural = "Expense Categories"
    
    def __str__(self):
        return self.name
    
class expense(models.Model):
    date = models.DateField()
    name = models.TextField(max_length = 200)
    amount = models.FloatField(default = 0)
    category = models.ForeignKey('expense_category', on_delete = models.RESTRICT, 
                                 null = True, blank = True, related_name='category')
    description = models.TextField(max_length = 1000, help_text = 'enter a description', blank = True, null = True)  
    
    class Meta:
        ordering = ['-date', 'category', 'name']

    def __str__(self):
        return self.name
    

def statement_fn(instance, filename):
    if instance.cleansed:
        folder = 'cleansed'
    else:
        folder = 'raw'
    return '/'.join(['bank_statements', folder, filename])

def fix_saving(x):
    if ('Van Oranje' in x.Mededelingen):
        x.af_bij = 'Af'
        x.amount = -x.amount
    return x


class ing_statement(models.Model):
    cleansed = models.BooleanField(default = False)
    generated_on = models.DateTimeField(auto_now_add=True)
    csv_file = models.FileField(upload_to = statement_fn, storage=OverwriteStorage(),
                                help_text = "ING bank statements", blank = True, null = True)
    
    class Meta:
        ordering = ['-generated_on']
        verbose_name = "ING statement"
        verbose_name_plural = "ING statements"
    
    def filename(self):
        return self.csv_file.name.split('/')[-1]
        
    def date_from(self):
        try:
            date_part = self.csv_file.name.replace('.csv', '').split('_')[-2]
            return dt.strptime(date_part, '%d-%m-%Y').date()
        except:
            return None
    
    def date_to(self):
        try:
            date_part = self.csv_file.name.replace('.csv', '').split('_')[-1]
            return dt.strptime(date_part, '%d-%m-%Y').date()
        except:
            return None
    
    def load_raw(self):
        if 'raw' in self.csv_file.name:
            raw_data = pd.read_csv(self.csv_file, sep=';').astype({'Bedrag (EUR)': 'string', 'Tag': 'string'})
            preprep_data = raw_data\
              .assign(
                Datum = pd.to_datetime(raw_data.Datum.astype('str')).dt.date,
                category = None, #raw_data.Tag.str.split(r'#| #| ', expand = True)[1],
                description = None #raw_data.Tag.str.split(r'#| #| ', expand = True)[2],
            ).rename(columns = col_rn)
            
            altered_saving = preprep_data.assign(
                amount = preprep_data.amount.str.replace(',','.')
            ).astype({'amount': 'float'}).apply(fix_saving, axis = 1)
            
            loaded_data = altered_saving.loc[altered_saving.af_bij == "Af"]\
             .groupby(['date', 'name', 'category', 'description'], dropna=False)\
             .aggregate({'amount':'sum'}).round(2)\
             .reset_index()[ing_cols]
            
            return loaded_data


    def __str__(self):
        return self.csv_file.name
    
    def get_absolute_url(self):
        """Returns the url to access a particular author instance."""
        return reverse('bank-statement-content', args=[str(self.id)])

    
class gas_readings(models.Model):
    date = models.DateField()
    reading = models.IntegerField()
    submitted = models.BooleanField(default = False)
    annual_statement = models.BooleanField(default = False)
    
    class Meta:
        ordering = ['-date']

    def __str__(self):
        return self.date
        
class electricity_readings(models.Model):
    date = models.DateField()
    reading_1 = models.IntegerField()
    reading_2 = models.IntegerField()
    submitted = models.BooleanField(default = False)
    annual_statement = models.BooleanField(default = False)
    
    class Meta:
        ordering = ['-date']

    def __str__(self):
        return self.date
        
        
