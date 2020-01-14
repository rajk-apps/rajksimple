from django.contrib import admin

from .models import Account, Cause, Transaction


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    pass


@admin.register(Cause)
class CauseAdmin(admin.ModelAdmin):
    pass


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    pass
