import httplib
import json
import mock

from rdr_service.dao.dv_order_dao import DvOrderDao
from rdr_service.dao.participant_dao import ParticipantDao
from rdr_service.dao.participant_summary_dao import ParticipantSummaryDao
from rdr_service.fhir_utils import SimpleFhirR4Reader
from rdr_service.api_util import VIBRENT_FHIR_URL
from rdr_service.model.participant import Participant
from rdr_service.participant_enums import OrderShipmentStatus, OrderShipmentTrackingStatus
from test_data import load_test_data_json
from unit_test_util import FlaskTestBase
from werkzeug.exceptions import ServiceUnavailable


class DvOrderDaoTestBase(FlaskTestBase):

  def setUp(self):
    super(DvOrderDaoTestBase, self).setUp(use_mysql=True)

    self.post_delivery = load_test_data_json('dv_order_api_post_supply_delivery.json')
    self.put_delivery = load_test_data_json('dv_order_api_put_supply_delivery.json')
    self.post_request = load_test_data_json('dv_order_api_post_supply_request.json')
    self.put_request = load_test_data_json('dv_order_api_put_supply_request.json')
    self.dao = DvOrderDao()

    self.participant_dao = ParticipantDao()
    self.summary_dao = ParticipantSummaryDao()

    self.participant = Participant(
      participantId=123456789,
      biobankId=7
    )
    self.participant_dao.insert(self.participant)
    self.summary = self.participant_summary(self.participant)
    self.summary_dao.insert(self.summary)
    self.mayolink_response = {'orders': {'order': {
      'status': 'finished',
      'reference_number': 'barcode',
      'received': '2019-04-05 12:00:00',
      'number': '12345',
      'patient': {'medical_record_number': 'WEB1ABCD1234'}
    }}}

    mayolinkapi_patcher = mock.patch(
      'dao.dv_order_dao.MayoLinkApi',
      **{'return_value.post.return_value': self.mayolink_response}
    )
    mayolinkapi_patcher.start()
    self.addCleanup(mayolinkapi_patcher.stop)

  def test_insert_biobank_order(self):
    payload = self.send_post('SupplyRequest', request_data=self.post_request, expected_status=httplib.CREATED)
    request_response = json.loads(payload.response[0])
    location = payload.location.rsplit('/', 1)[-1]
    put_response = self.send_put('SupplyRequest/{}'.format(location), request_data=self.put_request)
    payload = self.send_post('SupplyDelivery', request_data=self.post_delivery, expected_status=httplib.CREATED)
    post_response = json.loads(payload.response[0])
    location = payload.location.rsplit('/', 1)[-1]
    put_response = self.send_put('SupplyDelivery/{}'.format(location), request_data=self.put_delivery)
    self.assertEquals(request_response['version'], 1)
    self.assertEquals(post_response['version'], 3)
    self.assertEquals(post_response['meta']['versionId'].strip('W/'), '"3"')
    self.assertEquals(put_response['version'], 4)
    self.assertEquals(put_response['meta']['versionId'].strip('W/'), '"4"')
    self.assertEquals(put_response['barcode'], 'SABR90160121INA')
    self.assertEquals(put_response['biobankOrderId'], '12345')
    self.assertEquals(put_response['biobankStatus'], 'Delivered')
    self.assertEquals(put_response['order_id'], 999999)

  def test_enumerate_shipping_status(self):
    fhir_resource = SimpleFhirR4Reader(self.post_request)
    status = self.dao._enumerate_order_shipping_status(fhir_resource.status)
    self.assertEquals(status, OrderShipmentStatus.SHIPPED)

  def test_enumerate_tracking_status(self):
    fhir_resource = SimpleFhirR4Reader(self.post_delivery)
    status = self.dao._enumerate_order_tracking_status(fhir_resource.extension.get(url=VIBRENT_FHIR_URL + 'tracking-status').valueString)
    self.assertEquals(status, OrderShipmentTrackingStatus.ENROUTE)

  @mock.patch('dao.dv_order_dao.MayoLinkApi')
  def test_service_unavailable(self, mocked_api):
    #pylint: disable=unused-argument
    def raises(*args):
      raise ServiceUnavailable()

    with self.assertRaises(ServiceUnavailable):
      mocked_api.return_value.post.side_effect = raises
      self.dao.send_order(self.post_delivery, self.participant.participantId)







