""" HTML-serving views and JSON APIs.

Jin Cheng, 02/12/16
"""

from datetime import datetime
import dateutil.parser
import re

from django.shortcuts import render
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.authentication import SessionAuthentication, BasicAuthentication

from .serializers import CalorimeterSerializer, RunSerializer, DataPointSerializer
from .models import Calorimeter, Run, DataPoint


def IndexView(request):
    """
    Serves index HTML document as the HTTP response to any browser (non-API) request.
    :param request: Django HTTPRequest object
    :return: Django HTTPResponse object, containing the HTML body and metadata
    """
    return render(request, 'index.html', {})


class DeviceAccessPermission(permissions.BasePermission):
    """
    Permission check done with every HTTP request.

    Should be implemented with all API points to prevent abuse.
    Comment out implementations of this permission class in testing, as entering this code several times
        can get extremely tedious.
    """

    def has_object_permission(self, request, view, obj):
        if request.method == 'GET':
            try:
                access_code = request.GET['access_code']
            except KeyError:
                return False
        else:
            try:
                access_code = request.data['access_code']
            except KeyError:
                return False
        return access_code == obj.access_code


class CalorimeterStatusAPI(APIView):
    """
    Gives or updates JSONified data about the status of a single calorimeter.
    """
    # permission_classes = (DeviceAccessPermission, )

    def get_object(self):
        # for now, fix this to always return one single calorimeter.
        calorimeter = Calorimeter.objects.get(id=1)
        # self.check_object_permissions(self.request, calorimeter)
        return calorimeter

    def get(self, request, format=None):
        calorimeter = self.get_object()
        serializer = CalorimeterSerializer(calorimeter)
        return Response(serializer.data)

    def put(self, request, format=None):
        calorimeter = self.get_object()
        serializer = CalorimeterSerializer(calorimeter, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RunListAPI(APIView):
    """
    Gives a list of all runs conducted by a calorimeter, or create a new run to be started immediately.
    """
    # permission_classes = (DeviceAccessPermission, )

    def get(self, request, format=None, **kwargs):
        runs = Run.objects.filter(**kwargs)
        serializer = RunSerializer(runs, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = RunSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CsrfExemptSessionAuthentication(SessionAuthentication):
    """
    Django and Django REST framework by default requires all POST requests to include a X-CSRFToken header,
    which is not applicable for when the raspberry pi sends data
    because it won't have any existing response from an active session.

    The enforce_csrf method is overridden to circumvent the CSRF check.
    """

    def enforce_csrf(self, request):
        return


def datetime_parser(raw_input):
    """
    Parses a raw string input using tools. Tests its format by regex and initiates appropriate datetime constructor.

    :param raw_input: any string representation of datetime, in either POSIX or ISO format
    :return: a Python datetime object
    """

    # if input is a number, convert this POSIX timestamp to a Python datetime object
    if re.match(r'^[+-]?[0-9]*[.]?[0-9]+$', raw_input):
        since = datetime.fromtimestamp(float(raw_input))

    # else assume it is ISO formatted time string
    else:
        since = dateutil.parser.parse(raw_input)
    return since


class DataPointListAPI(APIView):
    """
    Gives a list of all data points for a specific run measured after a specified time.
    """

    # permission_classes = (DeviceAccessPermission, )
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication,)

    def get(self, request, format=None):
        """
        Get data points for a run (with its ID specified in GET parameter `run`),
        and after a certain time (with POSIX timestamp or ISO formatted string, optional).
        :return: JSON Response
        """
        try:
            kwargs = {
                'run_id': request.GET['run'],
            }
        except KeyError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if 'since' in request.GET:
            kwargs['measured_at__gte'] = datetime_parser(request.GET['since'])

        data_points = DataPoint.objects.filter(**kwargs)
        serializer = DataPointSerializer(data_points, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        """
        Main entry point for raspberry pi DSC device.
        Periodically receives data points measured on-device, containing a list of data point dicts.
        The dict should contain info on: time measured, temperatures (ref and sample), heat used (ref and sample).

        Time measured: should be either POSIX time or ISO formatted string
        Temperatures, heat outputss: floats

        :return: JSON Response, containing the Calorimeter stop flag (Bool), errors (List), data points (List).
        The stop flag, if true, should instruct the device to immediately stop heating or cooling.
        The error list will be empty if no error is found.
        """
        data_points = request.data.get('data_point') or request.data.get('data') or request.data.get('data_points')

        response = {
            'errors': [],
            'data_point': [],
        }
        # Batch create new data points
        for data_point in data_points:
            serializer = DataPointSerializer(data=data_point)
            if serializer.is_valid():
                serializer.save()
                response['data_point'].append(serializer.data)
            else:
                response['errors'].append(serializer.errors)

        # Calorimeter related operations also go here,
        # so that the device does not need to send multiple HTTP requests
        last_data_point = data_points[-1]
        calorimeter = Run.objects.get(id=last_data_point['run']).calorimeter

        # If a stop flag is set in the database (instructed by user on browser page),
        # send stop flag to device and reset this flag
        response['stop_flag'] = calorimeter.stop_flag
        calorimeter.stop_flag = False

        # Change this calorimeter's last communication time and temperatures
        # so that we can determine whether it's actively connected to the server
        # and display semi-real-time temp to user
        calorimeter.last_comm_time = timezone.now()
        calorimeter.current_ref_temp = last_data_point['temp_ref']
        calorimeter.current_sample_temp = last_data_point['temp_sample']
        calorimeter.save()

        if response['errors']:
            return Response(response, status.HTTP_400_BAD_REQUEST)
        return Response(response)
