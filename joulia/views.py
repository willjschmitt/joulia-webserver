from django.http import HttpResponse


def hello_world(request):
    """Returns simple Hello World HTML page.

    Kubernetes needs a root URL responding with a 200 status. This allows the
    setting up of an endpoint with a generic no-op response.
    """
    del request
    return HttpResponse('<html><body><h1>Hello, World</h1></body></html>')
