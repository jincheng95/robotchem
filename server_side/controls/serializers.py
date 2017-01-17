""" JSON serializers for database models.
Classes here parses python objects into JSON formats to be transmitted with HTTP requests to the Pi
or to client Javascript code.

Jin Cheng, 02/12/16
"""

from django.utils import timezone
from rest_framework import serializers

from .models import Calorimeter, Run, DataPoint


class CalorimeterSerializer(serializers.ModelSerializer):
    is_active = serializers.SerializerMethodField('is_calorimeter_active')
    has_active_runs = serializers.SerializerMethodField('check_active_runs')

    class Meta:
        model = Calorimeter
        fields = ('id', 'serial', 'access_code', 'name', 'creation_time',
                  'current_sample_temp', 'current_ref_temp',
                  'K_p', 'K_i', 'K_d', 'idle_loop_interval',
                  'active_loop_interval', 'web_api_min_upload_length',
                  'last_changed_time', 'last_comm_time',
                  'is_active', 'has_active_runs',
                  )
        read_only_fields = ('access_code', )

    def __init__(self, *args, **kwargs):
        super(CalorimeterSerializer, self).__init__(*args, **kwargs)
        self.from_device = False
        if 'from_device' in kwargs:
            if kwargs['from_device']:
                self.from_device = True

    def is_calorimeter_active(self, instance):
        time_delta = instance.last_comm_time - timezone.now()
        return abs(time_delta.total_seconds()) < 60

    def check_active_runs(self, instance):
        kwargs = {'calorimeter': instance, 'is_finished': False}
        if Run.objects.filter(**kwargs).exists():
            active_run = Run.objects.filter(**kwargs).order_by('-start_time')[0]
            return RunSerializer(active_run).data
        return False

    def update(self, instance, validated_data):
        instance.last_comm_time = timezone.now()
        super(CalorimeterSerializer, self).update(instance, validated_data)
        return instance


class DataPointSerializer(serializers.ModelSerializer):
    measured_at = serializers.DateTimeField(input_formats=['iso-8601'])
    run = serializers.PrimaryKeyRelatedField(queryset=Run.objects.all(), validators=[])

    class Meta:
        model = DataPoint
        fields = ('measured_at', 'received_at',
                  'temp_ref', 'temp_sample',
                  'heat_ref', 'heat_sample',
                  'run',
                  )


class RunSerializer(serializers.ModelSerializer):
    calorimeter = serializers.PrimaryKeyRelatedField(queryset=Calorimeter.objects.all(), validators=[])
    data_point_count = serializers.SerializerMethodField('count_data_points')

    class Meta:
        model = Run
        fields = ('id', 'name', 'creation_time', 'start_time', 'finish_time',
                  'is_ready', 'is_running', 'is_finished', 'email',
                  'start_temp', 'target_temp', 'ramp_rate',
                  'calorimeter', 'data_point_count',
                  )

    def count_data_points(self, instance):
        return instance.datapoint_set.count()
