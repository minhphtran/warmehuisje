from .models import ing_cols, expense
from django.db.models import Max, Sum, F, Q
import pandas as pd

def df_convert(x):
    if list(x.columns) != ing_cols:
        raise ValueError('Data columns misfit')
    x = x.where(pd.notnull(x), '')
    return x.reset_index().to_dict('records')


def get_stats(period_expense, cat, selected):
    if cat == 'total':
        filtered_expense = period_expense.filter(category__name__in = selected).filter(~Q(category__name = 'savings'))
    else:
        filtered_expense = period_expense.filter(category__name = cat)
    
    sum_expense = filtered_expense.aggregate(Sum('amount')).get('amount__sum')
    return sum_expense
        

def iterate_categories(cat, expenses, compare_expenses, selected):
    sum_expenses = get_stats(expenses, cat, selected) or 0
    sum_compare_expenses = get_stats(compare_expenses, cat, selected) or 0

    diff = sum_expenses - sum_compare_expenses
    if diff > 0:
        diff_ms = '+{}<i class="fa fa-angle-double-up red" aria-hidden="true"></i>'
        if cat == "savings":
            diff_ms = '+{}<i class="fa fa-angle-double-up pink" aria-hidden="true"></i>'
    elif diff < 0:
        diff_ms ='{}<i class="fa fa-angle-double-down pink" aria-hidden="true"></i>'
        if cat == "savings":
            diff_ms = '{}<i class="fa fa-angle-double-up red" aria-hidden="true"></i>'
    else:
        diff_ms = '<i class="fa fa-exchange" aria-hidden="true"></i>'
    
    if cat == "savings":
        title = "Savings<br><h4>(depo-withdraw)</h4>"
    elif cat == "total":
        title = "Total selected<br><h4>(excl. saving)</h4>"
    else:
        title = cat.capitalize()

    output = {'cat': title, 'sum': round(sum_expenses, 2), 
              'diff': diff_ms.format(round(diff, 2))}
    return output

def get_last_date():
    max_date = expense.objects.aggregate(Max('date')).get('date__max')
    return max_date


def format_ctx(ctx_dict, compare_dates, duration):
    try:
        max_date = get_last_date().strftime('%b %d')
    except:
        max_date = "undefined"
    ctx_dict[2].update({'txt' : "* last recorded on {} <br> * selected {} days".format(max_date, duration)})
    ctx_dict[3].update({'txt' : "* in comparison to expenses {} &#8594; {}".format(
        compare_dates[0].strftime('%b %d'),compare_dates[1].strftime('%b %d'))})
    [ctx_dict[i].update({'indx': i}) for i in range(len(ctx_dict))]
    
    return ctx_dict

def create_html_table(x):
    if list(x.columns) != ing_cols:
        raise ValueError('Misfit data')
    x = x.where(pd.notnull(x), '')
    
    head_data = ''
    for c in ing_cols:
        head_data += '\n      <th>'.format(c) + c + '</th>'
    head = '<thead>\n    <tr style="text-align: right;">' + head_data + '\n    </tr>\n  </thead>'

    row_data = ''
    for i in range(x.shape[0]):
        row_data += '<tr>\n      '
        for j in range(x.shape[1]):        
            if j == 4:
                attr = '<td class="custom-select sources" data-id="category-{}" data-type="category">'.format(i) + str(x.iloc[i,j])
            elif j == 5:
                attr = '<td class="editable" id="description-{}" data-type="description">'.format(i) + "<input type=text' class='input-data' value='" + str(x.iloc[i,j]) + "' class='form-control'>"
            else:
                attr = '<td>' + str(x.iloc[i,j])
            row_data += '\n' + attr + '</td>'     
        row_data += '</tr>\n  '
    rows = '<tbody>\n    ' + row_data + '\n    </tbody>'

    html = '\n '.join(['<table class="table-container" id="statement-table">', head, rows, '</table>'])

    return html

