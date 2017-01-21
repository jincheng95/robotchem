""" HTML-serving views and JSON APIs.

Jin Cheng, 02/12/16
"""

import csv
import re
from datetime import datetime

import dateutil.parser
from django.core.mail import send_mail
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotAllowed
from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string
from django.utils import timezone
from rest_framework import status, permissions
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import RetrieveUpdateDestroyAPIView

from server_side.rfsite.settings import DEBUG
from server_side.controls.models import Calorimeter, Run, DataPoint
from server_side.controls.serializers import CalorimeterSerializer, RunSerializer, DataPointSerializer


def IndexView(request, *args, **kwargs):
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
    """

    def has_object_permission(self, request, view, obj):
        if DEBUG:
            return True

        if request.method in ('GET', 'DELETE',):
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

    def has_permission(self, request, view):
        return self.has_object_permission(request, view, obj=Calorimeter.objects.get(pk=1))


class CalorimeterStatusAPI(APIView):
    """
    Gives or updates JSONified data about the status of a single calorimeter.
    """
    permission_classes = (DeviceAccessPermission, )

    def get_object(self):
        # for now, fix this to always return one single calorimeter.
        calorimeter = Calorimeter.objects.get(id=1)
        self.check_object_permissions(self.request, calorimeter)
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
        Run.objects.filter(is_finished=False).update(finish_time=timezone.now())
        Run.objects.filter(calorimeter=calorimeter).update(is_finished=True, is_running=False)
        return Response(status=status.HTTP_202_ACCEPTED)


class RunListAPI(APIView):
    """
    Gives a list of all runs conducted by a calorimeter, or create a new run to be started immediately.
    """
    permission_classes = (DeviceAccessPermission, )

    def get(self, request, format=None, **kwargs):
        runs = Run.objects.filter(creation_time__gte="2017-01-21", **kwargs).order_by('-creation_time')
        paginator = Paginator(runs, 5)
        page = request.GET.get('page')

        try:
            runs = paginator.page(page)
        except PageNotAnInteger:
            runs = paginator.page(1)
        except EmptyPage:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = RunSerializer(runs, many=True)
        data = {
            'page': page,
            'num_pages': paginator.num_pages,
            'runs': serializer.data,
        }
        return Response(data)

    def post(self, request, format=None):
        serializer = RunSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RunDetailsAPI(RetrieveUpdateDestroyAPIView):
    """
    Gives details about a Run, or changes the Run parameters, or delete the Run completely.
    """
    authentication_classes = (DeviceAccessPermission, )
    queryset = Run.objects.all()
    serializer_class = RunSerializer


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

    permission_classes = (DeviceAccessPermission, )
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

    def put(self, request, format=None):
        """Toggles a run's `is_ready` param,
        which indicates whether it has an inserted sample and should heat beyond the start temp."""
        try:
            run_id = request.data['run']
            run = Run.objects.get(id=run_id)
        except KeyError:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except Run.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if run.stabilized_at_start:
            run.is_ready = not run.is_ready
        else:
            run.is_ready = False
        run.save()
        return Response(RunSerializer(run).data)

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
        try:
            data_points = request.data['data']
            run_id = request.data['run']
            stabilized = request.data['stabilized_at_start']
            is_finished = request.data['is_finished']

        except KeyError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

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

        run = Run.objects.get(id=run_id)
        run.stabilized_at_start = stabilized
        response['is_ready'] = run.is_ready

        if not run.is_running and not run.is_finished and last_sample_temp >= run.start_temp:
            run.is_running = True
            run.start_time = timezone.now()
        if not run.is_finished and run.is_running and is_finished:
            run.is_running = False
            run.is_finished = True
            run.finish_time = timezone.now()

            if run.email:
                context = {
                    'run_name': run.name or "Run #{0}".format(run.id),
                    'run_url': 'http://robotchem.chengj.in/history/{0}/'.format(run_id),
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
    """On-the-fly generation of CSV data files and HTTP attachment response to client's download request."""

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
