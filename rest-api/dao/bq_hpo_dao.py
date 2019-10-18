import logging

from sqlalchemy.sql import text

from dao.bigquery_sync_dao import BigQuerySyncDao, BigQueryGenerator
from model.bq_base import BQRecord
from model.bq_hpo import BQHPOSchema, BQHPO
from model.hpo import HPO


class BQHPOGenerator(BigQueryGenerator):
  """
  Generate a HPO BQRecord object
  """

  def make_bqrecord(self, hpo_id, convert_to_enum=False):
    """
    Build a BQRecord object from the given hpo id.
    :param hpo_id: Primary key value from hpo table.
    :param convert_to_enum: If schema field description includes Enum class info, convert value to Enum.
    :return: BQRecord object
    """
    ro_dao = BigQuerySyncDao(backup=True)
    with ro_dao.session() as ro_session:
      row = ro_session.execute(text('select * from hpo where hpo_id = :id'), {'id': hpo_id}).first()
      data = ro_dao.to_dict(row)
      return BQRecord(schema=BQHPOSchema, data=data, convert_to_enum=convert_to_enum)

def bq_hpo_update(project_id=None):
  """
  Generate all new HPO records for BQ. Since there is called from a tool, this is not deferred.
  :param project_id: Override the project_id
  """
  ro_dao = BigQuerySyncDao(backup=True)
  with ro_dao.session() as ro_session:
    gen = BQHPOGenerator()
    results = ro_session.query(HPO.hpoId).all()

  w_dao = BigQuerySyncDao()
  with w_dao.session() as w_session:
    logging.info('BQ HPO table: rebuilding {0} records...'.format(len(results)))
    for row in results:
      bqr = gen.make_bqrecord(row.hpoId)
      gen.save_bqrecord(row.hpoId, bqr, bqtable=BQHPO, w_dao=w_dao, w_session=w_session, project_id=project_id)