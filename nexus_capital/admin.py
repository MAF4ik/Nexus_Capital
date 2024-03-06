from django.contrib import admin
from nexus_capital.models import *

admin.site.register(BankUser)
admin.site.register(Account)
admin.site.register(Service)
admin.site.register(Transaction)
admin.site.register(MobilePayment)
admin.site.register(UtilityPayment)
admin.site.register(Card)
admin.site.register(ServiceCategory)
