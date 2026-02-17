from django.core.management.base import BaseCommand
from game.services.analytics import get_platform_metrics
import json

class Command(BaseCommand):
    help = 'Displays platform revenue and growth metrics'

    def handle(self, *args, **options):
        stats = get_platform_metrics()
        
        self.stdout.write(self.style.SUCCESS('\n=== RPS ARENA PLATFORM STATS ==='))
        
        self.stdout.write(f"\n💰 REVENUE")
        self.stdout.write(f"  Total Stars: {stats['revenue']['total_stars']}")
        self.stdout.write(f"  Today's Stars: {stats['revenue']['today_stars']}")
        self.stdout.write(f"  Total Rake (Coins): {stats['revenue']['total_rake_coins']}")
        
        self.stdout.write(f"\n👤 USERS")
        self.stdout.write(f"  Total Users: {stats['users']['total']}")
        self.stdout.write(f"  New Today: {stats['users']['new_today']}")
        
        self.stdout.write(f"\n🎮 ENGAGEMENT")
        self.stdout.write(f"  Total Matches: {stats['matches']['total']}")
        self.stdout.write(f"  Matches Today: {stats['matches']['active_today']}")
        
        self.stdout.write(self.style.HTTP_INFO(f"\nGenerated at: {stats['timestamp']}"))
        self.stdout.write(self.style.SUCCESS('================================\n'))
