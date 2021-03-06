from dateutil import parser
from dateutil.tz import tzutc
from sqlalchemy import String
from sqlalchemy.dialects.mysql import DATETIME
from sqlalchemy.types import DateTime, SmallInteger, TypeDecorator
from werkzeug.exceptions import BadRequest
from werkzeug.routing import BaseConverter, ValidationError

from rdr_service.query import PropertyType

_PROPERTY_TYPE_MAP = {
    "String": PropertyType.STRING,
    "Date": PropertyType.DATE,
    "DateTime": PropertyType.DATETIME,
    "UTCDateTime": PropertyType.DATETIME,
    "UTCDateTime6": PropertyType.DATETIME,
    "Enum": PropertyType.ENUM,
    "EnumZeroBased": PropertyType.ENUM,
    "Integer": PropertyType.INTEGER,
    "SmallInteger": PropertyType.INTEGER,
}


class Enum(TypeDecorator):
    """A type for a SQLAlchemy column based on a protomsg Enum provided in the constructor"""

    impl = SmallInteger

    def __init__(self, enum_type):
        super(Enum, self).__init__()
        self.enum_type = enum_type

    def __repr__(self):
        return "Enum(%s)" % self.enum_type.__name__

    def process_bind_param(self, value, dialect):  # pylint: disable=unused-argument
        return int(value) if value else None

    def process_result_value(self, value, dialect):  # pylint: disable=unused-argument
        return self.enum_type(value) if value else None


class EnumZeroBased(Enum):
    """A type for a SQLAlchemy column based on a protomsg Enum provided in the constructor.
       This implementation allows for 0's as a value."""

    def process_bind_param(self, value, dialect):  # pylint: disable=unused-argument
        return int(value) if value is not None else None

    def process_result_value(self, value, dialect):  # pylint: disable=unused-argument
        return self.enum_type(value) if value is not None else None


class MultiEnum(TypeDecorator):
    """
  A multi-value Enum type for simple uses.

  Data in this format cannot be searched easily and in most cases it is preferable to use a
  relationship table.
  """

    impl = String

    def __init__(self, enum_type, delimiter=",", max_length=80):
        super(MultiEnum, self).__init__(max_length)
        self.enum_type = enum_type
        self.delimiter = delimiter

    def __repr__(self):
        return "MultiEnum({})".format(self.enum_type.__name__)

    def process_bind_param(self, value, dialect):  # pylint: disable=unused-argument
        return self.delimiter.join([str(int(item)) for item in value]) if value else None

    def process_result_value(self, value, dialect):  # pylint: disable=unused-argument
        return (
            [self.enum_type(int(raw_value)) for raw_value in value.split(self.delimiter) if len(raw_value)]
            if value
            else None
        )


class UTCDateTime(TypeDecorator):
    impl = DateTime

    def process_bind_param(self, value, engine):
        # pylint: disable=unused-argument
        if isinstance(value, str):
            value = parser.parse(value)
        if value is not None and value.tzinfo:
            return value.astimezone(tzutc()).replace(tzinfo=None)
        return value


class UTCDateTime6(TypeDecorator):
    impl = DATETIME(fsp=6)

    def process_bind_param(self, value, engine):
        # pylint: disable=unused-argument
        if isinstance(value, str):
            value = parser.parse(value)
        if value is not None and value.tzinfo:
            return value.astimezone(tzutc()).replace(tzinfo=None)
        return value


def to_client_participant_id(participant_id):
    return "P%d" % participant_id


def from_client_participant_id(participant_id):
    if not participant_id.startswith("P"):
        raise BadRequest("Invalid participant ID: %s" % participant_id)
    try:
        return int(participant_id[1:])
    except ValueError:
        raise BadRequest("Invalid participant ID: %s" % participant_id)


class ParticipantIdConverter(BaseConverter):
    """ https://werkzeug.palletsprojects.com/en/1.0.x/routing/#custom-converters """
    def to_python(self, value):
        try:
            return from_client_participant_id(value)
        except BadRequest as ex:
            raise ValidationError(ex.description)

    def to_url(self, value):
        """ this function should return a string type """
        # Assume the client has already converted this.
        return str(value)


def get_property_type(prop):
    prop_property = getattr(prop, "property", None)
    if not prop_property:
        return None
    columns = getattr(prop_property, "columns", None)
    if not columns:
        return None
    property_classname = columns[0].type.__class__.__name__
    property_type = _PROPERTY_TYPE_MAP.get(property_classname)
    if not property_type:
        return None
    return property_type
