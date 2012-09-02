import logging

from tastypie.validation import FormValidation as TastypieFormValidation


__all__ = ["FormValidation"]

ERROR_MESSAGES = {
    "required": "required",
    "invalid": "invalid",
    "max_length": "invalid",
}


logger = logging.getLogger(__name__)


class FormValidation(TastypieFormValidation):

    def is_valid(self, bundle, request=None):
        """
        Performs a check on ``bundle.data``to ensure it is valid.

        If the form is valid, an empty list (all valid) will be returned. If
        not, a list of errors will be returned.
        """
        form_kwargs = self.form_args(bundle)
        form_kwargs.update({"user": request.user if request is not None else bundle.request.user})
        form = self.form_class(**form_kwargs)

        if form.is_valid():
            return {}

        # The data is invalid. Let's collect all the error messages & return
        # them.
        _errors = form.errors

        errors = []

        if _errors:
            for k, v in _errors.iteritems():
                for code in v:
                    errors.append({
                        "field": k,
                        "code": code,
                    })

        logger.debug("Invalid API Call data(%s) errors(%s)", form_kwargs, errors)

        return errors
