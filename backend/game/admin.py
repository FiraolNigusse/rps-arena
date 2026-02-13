from django.contrib import admin
from django.utils import timezone
from .models import User, Rating, Match, Transaction, Withdrawal


admin.site.register(User)
admin.site.register(Rating)
admin.site.register(Match)
admin.site.register(Transaction)


@admin.register(Withdrawal)
class WithdrawalAdmin(admin.ModelAdmin):
    list_display = ("user", "amount", "status", "requested_at")
    list_filter = ("status",)
    actions = ["approve_withdrawal"]

    def approve_withdrawal(self, request, queryset):
        for withdrawal in queryset:
            if withdrawal.status == "pending":
                withdrawal.status = "approved"
                withdrawal.processed_at = timezone.now()
                withdrawal.save()

                withdrawal.user.coins -= withdrawal.amount
                withdrawal.user.save()

        self.message_user(request, "Selected withdrawals approved.")
