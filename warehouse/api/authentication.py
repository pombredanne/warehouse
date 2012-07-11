import base64

from django.contrib.auth import authenticate

from tastypie.authentication import BasicAuthentication as TastypieBasicAuthentication


__all__ = ["BasicAuthentication"]


class BasicAuthentication(TastypieBasicAuthentication):

    def is_authenticated(self, request, **kwargs):
        if not request.META.get("HTTP_AUTHORIZATION"):
            if request.method in ["GET", "HEAD"]:
                return True

            return self._unauthorized()

        try:
            (auth_type, data) = request.META["HTTP_AUTHORIZATION"].split()
            if auth_type.lower() != "basic":
                return self._unauthorized()
            user_pass = base64.b64decode(data)
        except:
            return self._unauthorized()

        bits = user_pass.split(':', 1)

        if len(bits) != 2:
            return self._unauthorized()

        if self.backend:
            user = self.backend.authenticate(username=bits[0], password=bits[1])
        else:
            user = authenticate(username=bits[0], password=bits[1])

        if user is None:
            return self._unauthorized()

        if not self.check_active(user):
            return False

        request.user = user
        return True
