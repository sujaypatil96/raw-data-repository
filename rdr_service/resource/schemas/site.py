#
# This file is subject to the terms and conditions defined in the
# file 'LICENSE', which is part of this source code package.
#
from enum import Enum

from marshmallow import validate

from rdr_service.resource import Schema, SchemaMeta, fields

# TODO: Use the Enums in participant_enums.py
class SiteStatusEnum(Enum):
    """ The active scheduling status of a site. """
    UNSET = 0
    ACTIVE = 1
    INACTIVE = 2


class EnrollingStatusEnum(Enum):
    """ The actively enrolling status of a site. """
    UNSET = 0
    ACTIVE = 1
    INACTIVE = 2


class DigitalSchedulingStatusEnum(Enum):
    """ The status of a sites digital scheduling capability. """
    UNSET = 0
    ACTIVE = 1
    INACTIVE = 2


class ObsoleteStatusEnum(Enum):
    """ If an organization is obsolete but referenced in other tables. """
    ACTIVE = 0
    OBSOLETE = 1


class SiteSchema(Schema):
    hpo_id = fields.Int32()
    organization_id = fields.Int32()

    site_id = fields.Int32(required=False)
    site_name = fields.String(validate=validate.Length(max=255))
    # The Google group for the site; this is a unique key used externally.
    google_group = fields.String(validate=validate.Length(max=255))
    mayolink_client_number = fields.Int32(required=False)

    site_status = fields.EnumString(enum=SiteStatusEnum)
    site_status_id = fields.EnumInteger(enum=SiteStatusEnum)
    enrolling_status = fields.EnumString(enum=EnrollingStatusEnum)
    enrolling_status_id = fields.EnumInteger(enum=EnrollingStatusEnum)
    digital_scheduling_status = fields.EnumString(enum=DigitalSchedulingStatusEnum)
    digital_scheduling_status_id = fields.EnumInteger(enum=DigitalSchedulingStatusEnum)

    schedule_instructions = fields.String(validate=validate.Length(max=2048))
    schedule_instructions_es = fields.String(validate=validate.Length(max=2048))
    launch_date = fields.Date()
    notes = fields.Text()
    notes_es = fields.Text()
    latitude = fields.Float()
    longitude = fields.Float()
    time_zone_id = fields.String(validate=validate.Length(max=1024))
    directions = fields.Text()
    physical_location_name = fields.String(validate=validate.Length(max=1024))
    address_1 = fields.String(validate=validate.Length(max=1024))
    address_2 = fields.String(validate=validate.Length(max=1024))
    city = fields.String(validate=validate.Length(max=255))
    state = fields.String(validate=validate.Length(max=2))
    zip_code = fields.String(validate=validate.Length(max=10))
    phone_number = fields.String(validate=validate.Length(max=80))
    admin_emails = fields.String(validate=validate.Length(max=4096))
    link = fields.String(validate=validate.Length(max=255))
    is_obsolete = fields.EnumString(enum=ObsoleteStatusEnum)
    is_obsolete_id = fields.EnumInteger(enum=ObsoleteStatusEnum)

    class Meta:
        """
        schema_meta info declares how the schema and data is stored and organized in the Resource database tables.
        """
        ordered = True
        resource_pk_field = 'site_id'
        # SchemaMeta (unique type id, unique type name, type URI, resource pk field, nested schemas)
        schema_meta = SchemaMeta(
            1030,
            'site',
            'Site',
            'site_id'
        )