from django.urls import path
from . import views

app_name = 'reservations'

urlpatterns = [
    path('book/', views.ReservationCreateView.as_view(), name='book'),
    path('my-reservations/', views.ReservationListView.as_view(), name='reservation_list'),
]
