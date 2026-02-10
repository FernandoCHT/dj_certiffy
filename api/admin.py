from django.contrib import admin

from api.models import Sale, CreditAssignment


# Register your models here.

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
  list_display = (
    'remission',
    'subtotal',
    'tax',
    'created_at',
  )

@admin.register(CreditAssignment)
class CreditAssignmentAdmin(admin.ModelAdmin):
  list_display = (
    'remission',
    'amount',
    'reason',
    'created_at',
  )
