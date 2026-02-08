from django.contrib import admin
from .models import User, Rating, Match, Transaction, Withdrawal

admin.site.register(User)
admin.site.register(Rating)
admin.site.register(Match)
admin.site.register(Transaction)
admin.site.register(Withdrawal)


# Register your models here.
