from django import forms
from .models import expense_category
import datetime as dt


class upload_statement_form(forms.Form):
    file = forms.FileField(widget=forms.FileInput(attrs={'accept': ".csv"}))
    
class check_expense_form(forms.Form):
    categories = forms.ModelMultipleChoiceField(queryset = expense_category.objects.all(),
                                           widget = forms.CheckboxSelectMultiple(attrs={'class': "category-picker hide"
                                                        })
                                               )
    date_from = forms.DateField(label = 'Start date', 
                                widget = forms.DateInput(attrs={'class': "date-picker",
                                                                'type': 'date'
                                                        })
                               )
    date_to = forms.DateField(label = 'End date', 
                              widget = forms.DateInput(attrs={'class': "date-picker",
                                                                'type': 'date'
                                                        })
                             )
                             
class upload_reading_form(forms.Form):
     date = forms.DateField(label = "Date",
         widget = forms.DateInput(attrs={'class': "date-picker",
                                         'type': 'date'
                                 })
     )
     gas_reading = forms.IntegerField(label = "Gas")
     electricity_reading_1 = forms.IntegerField(label = "Eletricity 1")
     electricity_reading_2 = forms.IntegerField(label = "Eletricity 2")
     submitted = forms.BooleanField(label = "Submitted to supplier?")
     statement = forms.BooleanField(label = "Part of annual statement?")
     
         