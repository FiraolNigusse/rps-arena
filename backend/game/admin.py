from django.contrib import admin
from django.utils import timezone
from .models import User, Rating, Match, Transaction, Withdrawal, PlatformRevenue
from .services.wallet import unlock_coins


admin.site.register(Rating)
admin.site.register(Transaction)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "telegram_id", "coins", "locked_coins", "is_flagged", "is_banned")
    list_filter = ("is_flagged", "is_banned")
    search_fields = ("username", "telegram_id")


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ("id", "player1", "player2", "stake", "winner", "status", "created_at")
    list_filter = ("status",)


@admin.register(PlatformRevenue)
class PlatformRevenueAdmin(admin.ModelAdmin):
    list_display = ("id", "amount", "match", "created_at")
    list_filter = ("created_at",)
    readonly_fields = ("created_at",)


@admin.register(Withdrawal)
class WithdrawalAdmin(admin.ModelAdmin):
    list_display = ("user", "amount", "status", "requested_at", "processed_at")
    list_filter = ("status",)
    actions = ["approve_withdrawals", "reject_withdrawals"]

    def approve_withdrawals(self, request, queryset):
        count = 0
        for w in queryset.filter(status="pending"):
            if w.user.locked_coins >= w.amount:
                w.status = "approved"
                w.processed_at = timezone.now()
                w.user.locked_coins -= w.amount
                w.user.save()
                w.save()
                count += 1
        self.message_user(request, f"Approved {count} withdrawal(s).")

    approve_withdrawals.short_description = "Approve selected"

    def reject_withdrawals(self, request, queryset):
        count = 0
        for w in queryset.filter(status="pending"):
            try:
                unlock_coins(w.user, w.amount)
                w.status = "rejected"
                w.processed_at = timezone.now()
                w.save()
                count += 1
            except ValueError:
                pass
        self.message_user(request, f"Rejected {count} withdrawal(s).")

    reject_withdrawals.short_description = "Reject selected"
