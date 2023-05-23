from django.urls import path, re_path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('stm/', views.ajax_view_expense, name = 'ajax-view-expense'),
    path('upload-bank-statement/', views.upload_bank_statement, name = 'bank-statement-upload'),
    path('check-where-our-money-went/', views.expense_view, name = 'expense-content'),
    path('upload-reading/', views.upload_reading, name = 'reading-upload'),
    re_path(r'^expense-show/(?P<cats>[-\w]+)/(?P<dfrom>[-\w]+)/(?P<dto>[-\w]+)/$', views.expense_edit, name='expense-edit'),
    path('bank-statement/<int:pk>', views.ing_statement_detail_view.as_view(), name='bank-statement-content'),
]