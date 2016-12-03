""" JSON serializers for database models.
Classes here parses python objects into JSON formats to be transmitted with HTTP requests to the Pi
or to client Javascript code.

Jin Cheng, 02/12/16
"""

from rest_framework import serializers
from django.utils import timezone
from .models import Calorimeter, Run, DataPoint


class CalorimeterSerializer(serializers.ModelSerializer):
    is_active = serializers.SerializerMethodField('is_calorimeter_active')

    class Meta:
        model = Calorimeter
        fields = ('id', 'serial', 'access_code', 'name', 'creation_time',
                  'current_sample_temp', 'current_ref_temp',
                  'last_changed_time', 'last_comm_time',
                  'is_active',
                  )

    def __init__(self, *args, **kwargs):
        super(CalorimeterSerializer, self).__init__(*args, **kwargs)
        self.from_device = False
        if 'from_device' in kwargs:
            if kwargs['from_device']:
                self.from_device = True

    def is_calorimeter_active(self, instance):
        time_delta = instance.last_comm_time - timezone.now()
        return time_delta.seconds < 60

    def last_comm(self, instance, validated_data):
        if self.from_device:
            instance.last_comm_time = timezone.now()
        return instance


class RunSerializer(serializers.ModelSerializer):
    class Meta:
        model = Run
        fields = ('id', 'name', 'creation_time', 'start_time',
                  'is_running', 'is_finished',
                  )


class DataPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataPoint
        fields = ('measured_at', 'received_at',
                  'temp_ref', 'temp_sample',
                  'heat_ref', 'heat_sample',
                  )

