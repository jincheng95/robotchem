""" HTML-serving views and JSON APIs.

Jin Cheng, 02/12/16
"""

from .serializers import CalorimeterSerializer, RunSerializer, DataPointSerializer
from .models import Calorimeter, Run, DataPoint
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions


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
        calorimeter = Calorimeter.objects.get(name="RPI3")
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

