""" HTML-serving views and JSON APIs.

Jin Cheng, 02/12/16
"""

import csv
from datetime import datetime
import dateutil.parser
import re

from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotAllowed
from django.core.mail import send_mail
from django.template.loader import render_to_string
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.authentication import SessionAuthentication, BasicAuthentication

from .serializers import CalorimeterSerializer, RunSerializer, DataPointSerializer
from .models import Calorimeter, Run, DataPoint
from rfsite.local_settings import EMAIL_ADDRESS, EMAIL_PASSWORD


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
        """Get serialized JSON response containing calorimeter status."""
        calorimeter = self.get_object()
        serializer = CalorimeterSerializer(calorimeter)
        return Response(serializer.data)

    def put(self, request, format=None):
        """Periodical updates from the device about its current temperatures when a job isn't running."""
        calorimeter = self.get_object()
        serializer = CalorimeterSerializer(calorimeter, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, format=None):
        """A non-standard implementation of the DELETE HTTP request,
        instructing the device to stop heating immediately."""
        calorimeter = self.get_object()
        calorimeter.stop_flag = True
        calorimeter.save()
        Run.objects.filter(is_finished=False).update(is_finished=True, finish_time=timezone.now())
        return Response(status=status.HTTP_202_ACCEPTED)


class RunListAPI(APIView):
    """
    Gives a list of all runs conducted by a calorimeter, or create a new run to be started immediately.
    """
    # permission_classes = (DeviceAccessPermission, )

    def get(self, request, format=None, **kwargs):
        runs = Run.objects.filter(**kwargs).order_by('-creation_time')
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
    if re.match(r'^[+-]?[0-9]*[.]?[0-9]+$', raw_input) or isinstance(raw_input, float) or isinstance(raw_input, int):
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
            kwargs['measured_at__gt'] = datetime_parser(request.GET['since'])

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
        data_points = request.data
        if not isinstance(data_points, list):
            return Response(status=status.HTTP_400_BAD_REQUEST)

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

        # Calorimeter + Run related operations also go here,
        # so that the device does not need to send multiple HTTP requests
        last_data_point = data_points[-1]
        last_sample_temp = last_data_point['temp_sample']
        run = Run.objects.get(id=last_data_point['run'])

        if not run.is_running and not run.is_finished and last_sample_temp >= run.start_temp:
            run.is_running = True
            run.started_at = timezone.now()
        if not run.is_finished and run.is_running and last_sample_temp >= run.target_temp:
            run.is_running = False
            run.is_finished = True
            run.finished_at = timezone.now()
            context = {
                'run_name': run.name or "Run #{0}".format(run.id),
                'run_url': 'http://robotchem.chengj.in/history/3/',
                'access_code': run.calorimeter.access_code,
            }
            body = render_to_string('run_completion_email_body.txt', context)
            subject = render_to_string('run_completion_email_title.txt', context)
            send_mail(subject, body, 'jinscheng@gmail.com', [run.email], fail_silently=True)

        # If a stop flag is set in the database (instructed by user on browser page),
        # send stop flag to device and reset this flag
        calorimeter = run.calorimeter
        stop_flag = calorimeter.stop_flag
        response['stop_flag'] = stop_flag
        if stop_flag:
            run.is_running, run.is_finished, run.finish_time = False, True, timezone.now()
        calorimeter.stop_flag = False

        # Change this calorimeter's last communication time and temperatures
        # so that we can determine whether it's actively connected to the server
        # and display semi-real-time temp to user
        calorimeter.last_comm_time = timezone.now()
        calorimeter.current_ref_temp = last_data_point['temp_ref']
        calorimeter.current_sample_temp = last_data_point['temp_sample']

        calorimeter.save()
        run.save()

        if response['errors']:
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        return Response(response)


def DataDownloadView(request, run_id):

    if request.method == 'POST':
        return HttpResponseNotAllowed

    try:
        file_format = request.GET['format']
    except KeyError:
        file_format = 'csv'

    if file_format == 'csv':
        run = get_object_or_404(Run, id=run_id)
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="{0}.csv"'.format(run.name or 'Run #'+run_id)

        data_points_by_measurement_time = DataPoint.objects.filter(run=run).order_by('measured_at')
        writer = csv.writer(response)
        writer.writerow(['Time', 'Temperature (sample)', 'Temperature (reference)',
                         'Heat Output (sample)', 'Heat Output (reference)'])
        time_origin = data_points_by_measurement_time[0].measured_at

        for dp in data_points_by_measurement_time:
            time_delta = dp.measured_at - time_origin
            writer.writerow([
                time_delta.total_seconds(),
                dp.temp_sample,
                dp.temp_ref,
                dp.heat_sample,
                dp.heat_ref,
            ])
        return response

    return HttpResponseBadRequest
