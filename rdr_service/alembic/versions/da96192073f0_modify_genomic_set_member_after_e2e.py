"""modify genomic_set_member after e2e

Revision ID: da96192073f0
Revises: b0520bacfbd0
Create Date: 2020-06-25 12:15:13.956804

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


# revision identifiers, used by Alembic.
revision = 'da96192073f0'
down_revision = 'b0520bacfbd0'
branch_labels = None
depends_on = None


def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_rdr():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('genomic_set_member', sa.Column('collection_tube_id', sa.String(length=80), nullable=True))
    op.add_column('genomic_set_member_history', sa.Column('collection_tube_id', sa.String(length=80), nullable=True))

    op.add_column('genomic_set_member', sa.Column('gc_site_id', sa.String(length=11), nullable=True))
    op.add_column('genomic_set_member_history', sa.Column('gc_site_id', sa.String(length=11), nullable=True))

    op.drop_constraint('genomic_set_member_ibfk_14', 'genomic_set_member', type_='foreignkey')

    op.drop_column('genomic_set_member', 'gem_ptsc_sent_job_run_id')
    op.drop_column('genomic_set_member_history', 'gem_ptsc_sent_job_run_id')

    op.drop_column('genomic_set_member', 'consent_for_ror')
    op.drop_column('genomic_set_member_history', 'consent_for_ror')

    op.drop_column('genomic_set_member', 'withdrawn_status')
    op.drop_column('genomic_set_member_history', 'withdrawn_status')
    # ### end Alembic commands ###


def downgrade_rdr():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('genomic_set_member', sa.Column('withdrawn_status', mysql.INTEGER(display_width=11),
                                                  autoincrement=False, nullable=True))
    op.add_column('genomic_set_member_history',
                  sa.Column('withdrawn_status', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True))

    op.add_column('genomic_set_member', sa.Column('consent_for_ror', mysql.VARCHAR(length=10), nullable=True))
    op.add_column('genomic_set_member_history', sa.Column('consent_for_ror', mysql.VARCHAR(length=10), nullable=True))

    op.add_column('genomic_set_member', sa.Column('gem_ptsc_sent_job_run_id', mysql.INTEGER(display_width=11),
                                                  autoincrement=False, nullable=True))
    op.add_column('genomic_set_member_history', sa.Column('gem_ptsc_sent_job_run_id', mysql.INTEGER(display_width=11),
                                                  autoincrement=False, nullable=True))

    op.create_foreign_key('genomic_set_member_ibfk_14', 'genomic_set_member', 'genomic_job_run', ['gem_ptsc_sent_job_run_id'], ['id'])

    op.drop_column('genomic_set_member', 'gc_site_id')
    op.drop_column('genomic_set_member_history', 'gc_site_id')

    op.drop_column('genomic_set_member', 'collection_tube_id')
    op.drop_column('genomic_set_member_history', 'collection_tube_id')
    # ### end Alembic commands ###


def upgrade_metrics():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade_metrics():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###
