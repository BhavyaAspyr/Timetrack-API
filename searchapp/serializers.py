from rest_framework import serializers
from timetrack.models import Timetrack  # Replace `Timetrack` with your model

class TimetrackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Timetrack
        fields = '__all__'
