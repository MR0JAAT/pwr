from rest_framework import serializers


class ForecastPointSerializer(serializers.Serializer):
    datetime = serializers.DateTimeField()
    demand_mw = serializers.FloatField(required=False)
    price_rs_per_mwh = serializers.FloatField(required=False)
