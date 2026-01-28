from django.urls import path
from .views import DemandForecast, PriceForecast, ModelMetrics

urlpatterns = [
    path('forecast/demand', DemandForecast.as_view()),
    path('forecast/price', PriceForecast.as_view()),
    path('model/metrics', ModelMetrics.as_view()),
]
