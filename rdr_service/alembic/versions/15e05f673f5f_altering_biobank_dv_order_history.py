"""Altering biobank_dv_order_history

Revision ID: 15e05f673f5f
Revises: f3fdb9d05ab3
Create Date: 2019-10-04 14:31:57.374442

"""
from alembic import op
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '15e05f673f5f'
down_revision = 'f3fdb9d05ab3'
branch_labels = None
depends_on = None


def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_rdr():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('bigquery_sync', 'project_id',
               existing_type=mysql.VARCHAR(length=80),
               nullable=True)
    # ### end Alembic commands ###

    # Procedure to remove the biobank_reference column and move data to correct columns of the history table
    # Make a bkup_ table
    op.execute(
        "CREATE TABLE bkup_biobank_dv_order_history AS SELECT * FROM biobank_dv_order_history;"
    )

    # PREP THE tmp_ TABLE
    # create the tmp_ table
    op.execute(
        "CREATE TABLE tmp_biobank_dv_order_history AS select * from biobank_dv_order_history LIMIT 1;"
    )

    # Clear the table
    op.execute(
        "TRUNCATE TABLE tmp_biobank_dv_order_history;"
    )

    # Add the `version` column
    op.execute(
        "ALTER TABLE tmp_biobank_dv_order_history ADD COLUMN version int(11) NOT NULL AFTER biobank_requisition;"
    )

    # Fill with data in the correct columns
    op.execute(
        """
        INSERT INTO tmp_biobank_dv_order_history
            (revision_action, revision_id, revision_dt, id, created,
             modified, participant_id, order_id, order_date, supplier, supplier_status,
             item_name, item_sku_code, item_snomed_code, item_quantity,
             street_address_1, street_address_2, city, state_id, zip_code,
             biobank_street_address_1, biobank_street_address_2, biobank_city, biobank_state_id,
             biobank_zip_code, shipment_last_update, tracking_id, biobank_tracking_id, order_type,
             order_status, shipment_carrier, shipment_est_arrival, shipment_status, barcode, biobank_order_id, 
             biobank_status, biobank_received, biobank_requisition, version)
        SELECT 
            revision_action, revision_id, revision_dt, id, created,
            modified, participant_id, order_id, order_date, supplier, supplier_status,
            item_name, item_sku_code, item_snomed_code, item_quantity,
            street_address_1, street_address_2, city, state_id, zip_code,
            biobank_street_address_1, biobank_street_address_2, biobank_city, biobank_state_id,
            biobank_zip_code, shipment_last_update, tracking_id, biobank_tracking_id, order_type,
            order_status, shipment_carrier, shipment_est_arrival, shipment_status, barcode, biobank_order_id, 
            biobank_reference, biobank_status, biobank_received, biobank_requisition
        FROM biobank_dv_order_history;
        """
    )

    # Remove the biobank_reference column
    op.execute(
        "ALTER TABLE tmp_biobank_dv_order_history DROP COLUMN biobank_reference;"
    )

    # Replace the current table with temp table data
    # first get rid of current table
    op.execute(
        "DROP TABLE biobank_dv_order_history;"
    )

    # create the table again based on tmp_ table data
    op.execute("CREATE TABLE biobank_dv_order_history AS SELECT * FROM tmp_biobank_dv_order_history;")

    # Clean out the tmp_ table
    op.execute("DROP TABLE tmp_biobank_dv_order_history;")

    # Removing the bkup_ table
    # op.execute("DROP TABLE bkup_biobank_dv_order_history;")

def downgrade_rdr():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('bigquery_sync', 'project_id',
               existing_type=mysql.VARCHAR(length=80),
               nullable=False)
    # ### end Alembic commands ###


def upgrade_metrics():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade_metrics():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###
