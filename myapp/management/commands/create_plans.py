from django.core.management.base import BaseCommand
from myapp.models import Plan

class Command(BaseCommand):
    help = 'Creates default subscription plans'

    def handle(self, *args, **kwargs):
        plans = [
            {
                'name': 'Free',
                'description': 'Basic access to articles and commenting features',
                'price': 0.00,
                'duration_days': 30,
                'features': {
                    'article_access': True,
                    'commenting': True,
                    'ad_free': False,
                    'exclusive_content': False,
                    'early_access': False,
                    'custom_badge': False,
                    'offline_reading': False,
                    'priority_support': False
                }
            },
            {
                'name': 'Premium',
                'description': 'Enhanced reading experience with ad-free browsing and exclusive content',
                'price': 15.00,
                'duration_days': 30,
                'features': {
                    'article_access': True,
                    'commenting': True,
                    'ad_free': True,
                    'exclusive_content': True,
                    'early_access': False,
                    'custom_badge': False,
                    'offline_reading': False,
                    'priority_support': True
                }
            },
            {
                'name': 'Pro',
                'description': 'Ultimate experience with all premium features plus early access and offline reading',
                'price': 29.00,
                'duration_days': 30,
                'features': {
                    'article_access': True,
                    'commenting': True,
                    'ad_free': True,
                    'exclusive_content': True,
                    'early_access': True,
                    'custom_badge': True,
                    'offline_reading': True,
                    'priority_support': True
                }
            }
        ]

        for plan_data in plans:
            plan, created = Plan.objects.get_or_create(
                name=plan_data['name'],
                defaults={
                    'description': plan_data['description'],
                    'price': plan_data['price'],
                    'duration_days': plan_data['duration_days'],
                    'features': plan_data['features']
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created plan: {plan.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Plan already exists: {plan.name}')) 