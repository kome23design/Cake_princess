# Cake Princess Restaurant Website

A premium, production-ready restaurant website built with Django and Tailwind CSS.

## Features
- **Modern UI/UX**: Premium design with gold and charcoal palette, glassmorphism, and AOS animations.
- **Full E-commerce**: Cart, checkout, and order tracking system.
- **Reservations**: Specialized booking for tables, surprises (birthdays, engagements), and events.
- **Admin Dashboard**: Comprehensive management of meals, orders, reservations, and reviews.
- **Localized**: Tailored for Yaounde, Cameroon with FCFA pricing and delivery integration.
- **Responsive**: Mobile-first design that looks stunning on all devices.

## Tech Stack
- Backend: Django 5.x, Django REST Framework
- Frontend: Django Templates, Tailwind CSS (via CDN), AOS.js
- Database: SQLite (ready for PostgreSQL)
- Deployment: Ready with WhiteNoise and Environment variables

## Getting Started
1. Clone the repository.
2. Create a virtual environment: `python -m venv venv`
3. Activate venv: `.\venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Linux/Mac)
4. Install dependencies: `pip install -r requirements.txt`
5. Run migrations: `python manage.py migrate`
6. Start the server: `python manage.py runserver`

## Admin Access
- URL: `/admin`
- Email: `admin@cakeprincess.com`
- Password: `admin123` (Please change this in production!)
