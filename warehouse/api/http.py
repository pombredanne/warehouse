from tastypie.http import HttpResponse


__all__ = ["HttpUnprocessableEntity"]


class HttpUnprocessableEntity(HttpResponse):
    status_code = 422
