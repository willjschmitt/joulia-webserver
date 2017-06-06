"""HTTP Utility functions for getting data out of HTTP requests.
"""

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseBadRequest
from django.http import HttpResponseNotFound
from django.http import HttpResponseForbidden


class HTTP400(Exception):
    pass


class HTTP403(Exception):
    pass


class HTTP404(Exception):
    pass


def get_data_value_or_400(request, key):
    """Gets the value for a data key if it exists. If it does not, raises
    Http400.

    Args:
        request: Django request with data in it.
        key: Post key for a value in the request.data.

    Returns:
        value for the key in the request.data data.

    Raises:
        Http400: if the key is not in the request data.
    """
    if key not in request.data:
        raise HTTP400('Missing {} in request.'.format(key))
    return request.data[key]


def get_object_or_404(model, pk):
    """Gets the object from the ``model`` with the provided ``pk``. If it does
    not exist raises Http404.

    Args:
        model: The model to query against.
        pk: The pk for the model to query.

    Returns:
        The model instance at pk.

    Raises:
        Http404: if the model instance does not exist.
    """
    try:
        obj = model.objects.get(pk=pk)
    except ObjectDoesNotExist as e:
        raise HTTP404(
            '{} instance not found.'.format(model)) from e
    else:
        return obj


class ConvertHTTPExceptionsMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
        except HTTP400 as e:
            return HttpResponseBadRequest(e)
        except HTTP403 as e:
            return HttpResponseForbidden(e)
        except HTTP404 as e:
            return HttpResponseNotFound(e)

        return response
