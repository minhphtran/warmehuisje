from django.contrib import admin

from .models import expense_category, expense, ing_statement


class expense_category_admin(admin.ModelAdmin):
    list_display = ('name', 'frequency')  
admin.site.register(expense_category, expense_category_admin)
    
class expense_admin(admin.ModelAdmin):
    list_display = ('date', 'name', 'amount', 'category', 'description')
    list_filter = ['category', 'date']  
admin.site.register(expense, expense_admin)    
    
class ing_statement_admin(admin.ModelAdmin):
    list_display = ('filename', 'date_from', 'date_to')
admin.site.register(ing_statement, ing_statement_admin)
