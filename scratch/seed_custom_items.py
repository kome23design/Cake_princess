import os
import django
import sys
from pathlib import Path
from django.core.files import File

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
sys.path.append(str(BASE_DIR / 'apps'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from menu.models import Category, MadeOnCommandItem
from django.utils.text import slugify

def seed_made_on_command():
    pastry_cat, _ = Category.objects.get_or_create(name='Pastries', defaults={'slug': 'pastries'})
    cake_cat, _ = Category.objects.get_or_create(name='Cakes', defaults={'slug': 'cakes'})

    items = [
        {
            'title': 'Exquisite French Pastries',
            'description': 'Intricately crafted with gold leaf and fresh berries. Perfect for upscale events.',
            'category': pastry_cat,
            'image_path': 'static/images/gallery/custom_pastry.png'
        },
        {
            'title': 'Sculpted Floral Cakes',
            'description': 'Highly detailed, custom sculpted cakes for your most luxurious celebrations.',
            'category': cake_cat,
            'image_path': 'static/images/gallery/special_cake.png'
        }
    ]

    for data in items:
        slug = slugify(data['title'])
        if not MadeOnCommandItem.objects.filter(slug=slug).exists():
            item = MadeOnCommandItem(
                title=data['title'],
                slug=slug,
                description=data['description'],
                category=data['category'],
                is_active=True
            )
            # Open the image file
            with open(data['image_path'], 'rb') as f:
                item.image.save(os.path.basename(data['image_path']), File(f), save=True)
            print(f"Created item: {data['title']}")

if __name__ == '__main__':
    seed_made_on_command()
