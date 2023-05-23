from django import template
from ..models import ing_cols

register = template.Library()

def process_elem(elem):
    i = elem.get('index')
    date = '\n<td>' + str(elem.get('date'))
    name = '\n<td>' + str(elem.get('name'))
    #af_bij = '\n<td>' + str(elem.get('af_bij'))
    amount = '\n<td>' + str(elem.get('amount'))
    category = '\n<td class="custom-select sources" data-id="category-{}" data-type="category">'.format(i) + str(elem.get('category'))
    description = '\n<td class="editable" id="description-{}" data-type="description">'.format(i) + "<input type=text' class='input-data' oninput='alert_saved();' value='" \
                    + str(elem.get('description')) + "' class='form-control'></td>"
    
    return '<tr>\n      ' + '</td>'.join([date, name, amount, category, description]) + '</tr>' #, af_bij

def dict_html(value):
    head_data = ''
    for c in ing_cols:
        head_data += '\n      <th>' + c + \
        '<a href="#" class="sort-table" id="sort-{}"><i class="fa fa-sort" id={}'.format(c, c) +\
        ' aria-hidden="true"></i></a></th>'
    head = '<thead>\n    <tr style="text-align: right;">' + head_data + '\n    </tr>\n  </thead>'

    rows = '\n '.join(['<tbody>'] + list(map(process_elem, value)) + ['</tbody>'])
    
    html = '\n '.join(['<table class="table-container" id="statement-table">', head, rows, '</table>'])

    return html

register.filter('dict_html', dict_html)
