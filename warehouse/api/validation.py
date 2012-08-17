from tastypie.validation import FormValidation as TastypieFormValidation


__all__ = ["FormValidation"]

ERROR_MESSAGES = {
    "required": "required",
    "invalid": "invalid",
    "already_exists": "already_exists",
    "max_length": "invalid",
}


class FormValidation(TastypieFormValidation):

    def is_valid(self, *args, **kwargs):
        _errors = super(FormValidation, self).is_valid(*args, **kwargs)

        errors = []

        if _errors:
            for k, v in _errors.iteritems():
                for code in v:
                    errors.append({
                        "field": k,
                        "code": code,
                    })

        return errors
