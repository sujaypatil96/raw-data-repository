"""change_ethnicity_for_workbench_researcher__model
Revision ID: 6d1953c656f6
Revises: e968d868a097
Create Date: 2020-02-05 15:48:19.210239
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '6d1953c656f6'
down_revision = 'e968d868a097'
branch_labels = None
depends_on = None


def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_rdr():
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute("ALTER TABLE `workbench_researcher` MODIFY `ethnicity` JSON;")
    op.execute("ALTER TABLE `workbench_researcher_history` MODIFY `ethnicity` JSON;")
    # ### end Alembic commands ###


def downgrade_rdr():
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute("ALTER TABLE `workbench_researcher` MODIFY `ethnicity` smallint(6);")
    op.execute("ALTER TABLE `workbench_researcher_history` MODIFY `ethnicity` smallint(6);")
    # ### end Alembic commands ###


def upgrade_metrics():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade_metrics():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###
