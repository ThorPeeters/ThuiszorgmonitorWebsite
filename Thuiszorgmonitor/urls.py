from django.urls import path
from Thuiszorgmonitor import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('Account/', views.account_view, name='Account'),
    path('', views.home, name='home'),
    path("Thuiszorgmonitor/", views.show_heartbeat, name="show_heartbeat"),
    path("Thuiszorgmonitor/", views.check_heartbeat, name="check_heartbeat"),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('live-chart/', views.live_chart, name='live_chart'),
]


