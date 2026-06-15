from django.urls import path
from . import views

app_name = 'menu'

urlpatterns = [
    path('', views.MenuListView.as_view(), name='menu_list'),
    path('category/<slug:slug>/', views.MenuListView.as_view(), name='category_detail'),
    path('meal/<slug:slug>/', views.MealDetailView.as_view(), name='meal_detail'),
    path('search/', views.MealSearchView.as_view(), name='meal_search'),
    path('custom-order/<slug:slug>/', views.MadeOnCommandDetailView.as_view(), name='custom_item_detail'),
]
