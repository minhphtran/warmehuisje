from django.template import RequestContext
from django.shortcuts import render, redirect
from django.conf import settings
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.http import Http404
from .forms import upload_statement_form, check_expense_form, upload_reading_form
from .models import expense_category, expense, ing_statement, ing_cols
from .utils import df_convert, iterate_categories, format_ctx, get_last_date
from django.core.files.base import ContentFile
from django.views.decorators.csrf import csrf_exempt
from django.views import generic
from io import StringIO
import pandas as pd
import datetime as dt
import re
import os
import json
from django.utils.timezone import datetime

#categories = {'value':[{'cat': cat.name} for cat in expense_category.objects.all()]}

def index(request):
     return render(request, 'index.html')

def process_record(row):
    try:
        expense_inst, created = expense.objects.get_or_create(date = row['date'], name = row['name'], 
                                                     amount = row['amount']
                                                    )
        if isinstance(expense_inst, expense):
            expense_inst = [expense_inst]
        for inst in expense_inst:
            if pd.notnull(row['category']):
                inst.category = expense_category.objects.get(name = row.category)
            if pd.isnull(row['description']):
                inst.description = None
            else:
                inst.description = row.description
            
            inst.save()
            
        return "success"
    except Exception as e:
        return str(e)

    
def retrieve_stats(cats, dfrom, dto):
    
    freq_cats = ['groceries', 'utilities', 'leisure']
    
    show_cats = ['total'] + cats + [c for c in freq_cats if c not in cats]

    
    expenses = expense.objects.filter(date__range=[dfrom, dto])
    period = (dto - dfrom).days 
    
    compare_from = (dfrom.replace(day = 1) - dt.timedelta(days=1)).replace(day = dfrom.day)
    compare_to = compare_from + dt.timedelta(period)
    
    compare_dates = [compare_from, compare_to]
    compare_expenses = expense.objects.filter(date__range = compare_dates)
    
    stats_dict = list(map(lambda cat: iterate_categories(cat, expenses, compare_expenses, cats),
                    show_cats[0:4]))

    stats_dict = format_ctx(stats_dict, compare_dates, period)
    return stats_dict

        
def expense_view(request):
    if request.method == 'GET':
        form = check_expense_form(request.GET)
        if form.is_valid():
            date_from = form.cleaned_data["date_from"]
            date_to = form.cleaned_data["date_to"]
            cat_objs = form.cleaned_data["categories"]
            categories = [c.name for c in cat_objs]
                
            try:  
                ## send to upload file
                if 'edit' in request.GET:

                    return redirect('expense-edit', cats = '-'.join([str(c.id) for c in cat_objs]), 
                                    dfrom = date_from, dto = date_to)
                
                ## show statistics
                if 'chart' in request.GET:
                    stats_dict = retrieve_stats(cats = categories, dfrom = date_from, dto = date_to)
 
                    form = check_expense_form(initial = {'date_from': date_from,
                                                         'date_to': date_to,
                                                         'categories': cat_objs
                                                        })

                    
                    return render(request, 'expenses/view_expense.html',
                                      {'form': form, 'stats': stats_dict}
                                     )

            except Exception as e:
                return JsonResponse({"fail": str(e)})

    date_to = datetime.today(); date_from = datetime.today()
    stats_dict = {}
    if expense.objects.exists():
        date_to = get_last_date()
        date_from = date_to.replace(day=1)
    if expense_category.objects.exists():
        stats_dict = retrieve_stats(cats=[cat.name for cat in expense_category.objects.all()],
                                    dfrom=date_from, dto=date_to)


    form = check_expense_form(initial={'categories': expense_category.objects.all(),
                                       'date_from': date_from,
                                       'date_to': date_to
                                       })
    
    return render(request, 'expenses/view_expense.html',
                  {'form': form, 'stats': stats_dict}
                 )


def expense_edit(request, cats, dfrom, dto):
    order_by = request.GET.get('order_by') or 'date'
    desc = request.GET.get('desc') == 'true'
    
    categories = expense_category.objects.filter(id__in = cats.split('-'))
    
    expenses = expense.objects.filter(date__range=[dfrom, dto]) 
    if len(categories)!=len(expense_category.objects.all()):
        expenses = expenses.filter(category__in = categories)

    if len(expenses) > 0:
        df = pd.DataFrame(list(expenses.values(
                            'date', 'name', 'amount', 'category__name', 'description'
                        ))).rename( columns={"category__name": "category"})
    else: 
        df = pd.DataFrame(columns = ing_cols)
    
    records = df_convert(df.sort_values([order_by], ascending = desc))
    paginator = Paginator(records, 7)
    pagenr = request.GET.get('page')
    page = paginator.get_page(pagenr)

    context = {'date_from': dfrom, 'date_to': dto, 'nrow': len(df),
               'page_obj': page, 'order_by': order_by, 'desc': desc, 
               'categories': json.dumps({'value':[{'cat': cat.name} for cat in expense_category.objects.all()]})
              }

    return render(request, 'expenses/ing_statement_detail.html', context)



@csrf_exempt
def ajax_view_expense(request):
    string_resp = request.POST.get('data','')
    #path = request.POST.get('fn','').replace('raw', 'cleansed')
    try:
        cleansed_data = pd.read_csv(StringIO(string_resp), sep = ';')
        resp = cleansed_data.astype({'name':'string', 'amount': 'float'})\
         .apply(lambda x: process_record(x), axis = 1)
        return JsonResponse({"abc": resp.to_json()})

        
#         cleansed_file = ing_statement.objects.get_or_create(csv_file = path, cleansed = True)
#         cleansed_file[0].csv_file.save(path.split('/')[-1], ContentFile(string_resp))
        #return JsonResponse({"success": 'yay'})
    except Exception as e:
        return JsonResponse({"fail": str(e)})


def upload_reading(request):
    form = upload_reading_form()
    return render(request, 'expenses/upload_reading.html', {'form': form})

@csrf_exempt    
def upload_bank_statement(request):

    if request.method == 'POST' and request.FILES:

        form = upload_statement_form(request.POST, request.FILES)
       
        if form.is_valid():
            statement_file = request.FILES['file']
            try:
                raw_file = ing_statement.objects.get(csv_file__endswith = statement_file.name, 
                                                     cleansed = False)
                raw_file.delete()
            except Exception as e:
                if 'it returned 2' in str(e):
                    ing_statement.objects.filter(csv_file__endswith = statement_file.name, 
                                                     cleansed = False).delete()
                else:
                    pass
                
            raw_file = ing_statement.objects.create(csv_file = statement_file, cleansed = False)
            return redirect(raw_file.get_absolute_url() + '#hash')


    form = upload_statement_form()
    try:
        max_date = get_last_date()
        ms = "The last recorded date is {}".format(max_date.strftime('%b %d'))
        if max_date < (dt.date.today() - dt.timedelta(days = 8)):
            ms += "<br> next <a href='https://mijn.ing.nl/login/' style='font-family: Muli;color:#572112;' target='_blank'>download</a> should be <b>{} &#8594; {}</b>".format(
                max_date + dt.timedelta(days=1), 
                dt.date.today() - dt.timedelta(days=1))
    except:
        ms = None
       
    return render(request, 'expenses/upload_bank_statement.html', {'form': form, 'ms': ms})



class ing_statement_detail_view(generic.DetailView):
    """Generic class-based detail view for an author."""
    model = ing_statement
    
    
    def get_context_data(self, **kwargs):
        order_by = self.request.GET.get('order_by') or 'date'
        desc = self.request.GET.get('desc') == 'true'
        
        # Call the base implementation first to get a context
        fn = self.object.csv_file.name
        #page = df_convert(self.object.load_raw().iloc[120:126])
        data = self.object.load_raw()\
            .sort_values([order_by], ascending = desc)
        records = df_convert(data)
        paginator = Paginator(records, 8)
        pagenr = self.request.GET.get('page')
        page = paginator.get_page(pagenr)
        
        nrow = len(data)
        record_count = len(expense.objects.all()) + nrow

        return {'date_from': self.object.date_from,
                'date_to': self.object.date_to,
                'nrow': len(data),
                'page_obj': page,
                'order_by': order_by,
                'desc': str(desc).lower(),
                'record_count': record_count,
                #'cleansed': fn,
                #'data': page.to_html(index=False, classes = "table-container"),
                #'data': create_html_table(page),
                #'data': process_dict(page),
                'categories': json.dumps({'value':[{'cat': cat.name} for cat in expense_category.objects.all()]})
               }

    
    
    
    