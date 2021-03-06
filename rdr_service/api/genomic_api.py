from dateutil import parser

from flask import request
from werkzeug.exceptions import NotFound, BadRequest

from rdr_service import clock
from rdr_service.api.base_api import BaseApi
from rdr_service.api_util import GEM, RDR_AND_PTC, RDR
from rdr_service.app_util import auth_required
from rdr_service.dao.genomics_dao import GenomicPiiDao, GenomicOutreachDao


class GenomicPiiApi(BaseApi):
    def __init__(self):
        super(GenomicPiiApi, self).__init__(GenomicPiiDao())

    @auth_required([GEM, RDR])
    def get(self, mode=None, p_id=None):
        if mode not in ('GEM', 'RHP'):
            raise BadRequest("GenomicPII Mode required to be \"GEM\" or \"RHP\".")

        if p_id is not None:
            pii = self.dao.get_by_pid(p_id)

            if not pii:
                raise NotFound(f"Participant with ID {p_id} not found")

            proto_payload = {
                'mode': mode,
                'data': pii
            }

            return self._make_response(proto_payload)

        raise BadRequest


class GenomicOutreachApi(BaseApi):
    def __init__(self):
        super(GenomicOutreachApi, self).__init__(GenomicOutreachDao())

    @auth_required(RDR_AND_PTC)
    def get(self, mode=None):
        if mode not in ('GEM', 'RHP'):
            raise BadRequest("GenomicOutreach Mode required to be \"GEM\" or \"RHP\".")

        if mode == "GEM":
            return self.get_gem_outreach()

        return BadRequest

    def get_gem_outreach(self):
        """
        Returns the GEM outreach resource based on the request parameters
        :return:
        """
        _start_date = request.args.get("start_date")
        _end_date = request.args.get("end_date")

        _pid = request.args.get("participant_id")

        if _pid is not None and _start_date is not None:
            raise BadRequest('Start date not supported with participant lookup.')

        # Set the return timestamp
        if _end_date is None:
            _end_date = clock.CLOCK.now()
        else:
            _end_date = parser.parse(_end_date)

        participant_report_states = None

        # If this is a participant lookup
        if _pid is not None:
            if _pid.startswith("P"):
                _pid = _pid[1:]

            participant_report_states = self.dao.participant_lookup(_pid)

            if len(participant_report_states) == 0:
                raise NotFound(f'Participant P{_pid} does not exist in the Genomic system.')

        # If this is a date lookup
        if _start_date is not None:
            _start_date = parser.parse(_start_date)

            participant_report_states = self.dao.date_lookup(_start_date, end_date=_end_date)

        if participant_report_states is not None:
            proto_payload = {
                'date': clock.CLOCK.now(),
                'data': participant_report_states
            }

            return self._make_response(proto_payload)

        return BadRequest
