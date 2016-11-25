from django.shortcuts import render


def IndexView(request):
    """
    Serves index HTML document as the HTTP response to any browser (non-API) request.
    :param request: Django HTTPRequest object
    :return: Django HTTPResponse object, containing the HTML body and metadata
    """
    return render(request, 'index.html', {})
