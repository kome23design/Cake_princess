import os
import django
import sys
from pathlib import Path

# Add the project root and apps directory to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
sys.path.append(str(BASE_DIR / 'apps'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from menu.models import Category, Meal
from django.utils.text import slugify

def seed():
    categories = [
        {'name': 'Cakes', 'description': 'Exquisite celebration and custom cakes.'},
        {'name': 'Pastries', 'description': 'French-inspired buttery pastries.'},
        {'name': 'Meals', 'description': 'Savory African and Continental dishes.'},
        {'name': 'Drinks', 'description': 'Refreshing juices and premium wines.'},
        {'name': 'Yogurt', 'description': 'Creamy, natural homemade yogurts.'},
        {'name': 'Event Packages', 'description': 'Specialized decor and catering bundles.'},
    ]

    for cat_data in categories:
        Category.objects.get_or_create(
            name=cat_data['name'],
            defaults={'slug': slugify(cat_data['name']), 'description': cat_data['description']}
        )

    print("Categories seeded.")

    # Add some demo meals
    cake_cat = Category.objects.get(name='Cakes')
    meal_cat = Category.objects.get(name='Meals')
    pastry_cat = Category.objects.get(name='Pastries')

    meals = [
        {
            'name': 'Royal Velvet Cake',
            'category': cake_cat,
            'description': 'A moist, velvety red cake layered with premium cream cheese frosting.',
            'price': 15000,
            'is_daily_special': True
        },
        {
            'name': 'Bastos Mixed Grill',
            'category': meal_cat,
            'description': 'Selection of grilled chicken, beef, and plantains with spicy Yaounde sauce.',
            'price': 7500,
            'is_daily_special': False
        },
        {
            'name': 'Golden Croissant',
            'category': pastry_cat,
            'description': 'Buttery, flaky, and golden-brown French croissant baked fresh every morning.',
            'price': 1500,
            'is_daily_special': True
        }
    ]

    for m in meals:
        Meal.objects.get_or_create(
            name=m['name'],
            defaults={
                'category': m['category'],
                'slug': slugify(m['name']),
                'description': m['description'],
                'price': m['price'],
                'is_daily_special': m['is_daily_special'],
                'is_available': True
            }
        )

    print("Demo meals seeded.")

if __name__ == '__main__':
    seed()
