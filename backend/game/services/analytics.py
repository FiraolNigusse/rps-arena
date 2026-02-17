from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from game.models import Payment, User, Match, PlatformRevenue

def get_platform_metrics():
    """
    Returns key performance indicators for the platform.
    """
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # 1. Revenue (Completed Payments)
    total_stars_revenue = Payment.objects.filter(status="completed").aggregate(Sum("amount"))["amount__sum"] or 0
    today_stars_revenue = Payment.objects.filter(status="completed", updated_at__gte=today_start).aggregate(Sum("amount"))["amount__sum"] or 0

    # 2. Match Rake (Platform Revenue table)
    total_rake = PlatformRevenue.objects.aggregate(Sum("amount"))["amount__sum"] or 0
    today_rake = PlatformRevenue.objects.filter(created_at__gte=today_start).aggregate(Sum("amount"))["amount__sum"] or 0

    # 3. User Growth
    total_users = User.objects.count()
    new_users_today = User.objects.filter(created_at__gte=today_start).count()

    # 4. Engagement
    total_matches = Match.objects.count()
    active_matches_today = Match.objects.filter(created_at__gte=today_start).count()

    return {
        "revenue": {
            "total_stars": total_stars_revenue,
            "today_stars": today_stars_revenue,
            "total_rake_coins": total_rake,
            "today_rake_coins": today_rake,
        },
        "users": {
            "total": total_users,
            "new_today": new_users_today,
        },
        "matches": {
            "total": total_matches,
            "active_today": active_matches_today,
        },
        "timestamp": now.isoformat()
    }
