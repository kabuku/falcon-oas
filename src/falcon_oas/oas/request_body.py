from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import jsonschema

from .exceptions import ValidationError


class RequestBodyUnmarshaler(object):
    def __init__(self, schema_unmarshaler):
        self._unmarshal_schema = schema_unmarshaler.unmarshal

    def unmarshal(self, request_body, request_body_spec_dict):
        if not request_body.content_length:
            if request_body_spec_dict.get('required', False):
                error = jsonschema.ValidationError(
                    'Request body is required',
                    validator='required',
                    validator_value=True,
                    schema=request_body_spec_dict,
                    schema_path=('required',),
                )
                return None, [error]
            return None, None

        # TODO: Let the validator handle the media error
        media = request_body.media
        media_type = request_body.media_type
        media_type_spec_dict = request_body_spec_dict['content'][media_type]
        try:
            unmarshaled = self._unmarshal(media, media_type_spec_dict)
        except ValidationError as e:
            for error in e.errors:
                error.schema_path.extendleft(['schema', media_type, 'content'])
            return None, e.errors
        else:
            return unmarshaled, None

    def _unmarshal(self, value, media_type_spec_dict):
        try:
            schema = media_type_spec_dict['schema']
        except KeyError:
            return value

        value = self._unmarshal_schema(value, schema)
        return value
