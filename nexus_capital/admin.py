from django.contrib import admin
from nexus_capital.models import BankUser, Account, Service, Transfer, Payment

admin.site.register(BankUser)
admin.site.register(Account)
admin.site.register(Service)
admin.site.register(Transfer)
admin.site.register(Payment)
