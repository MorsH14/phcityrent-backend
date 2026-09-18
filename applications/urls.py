from django.urls import path
from .views import ApplicationCreateView, MyApplicationsView, ApplicationDecisionView

urlpatterns = [
    path('', ApplicationCreateView.as_view(), name='application-create'),
    path('mine/', MyApplicationsView.as_view(), name='my-applications'),
    path('<int:pk>/decision/', ApplicationDecisionView.as_view(), name='application-decision'),
]