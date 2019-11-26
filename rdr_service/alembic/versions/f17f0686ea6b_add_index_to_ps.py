"""add index to PS

Revision ID: f17f0686ea6b
Revises: adb4ea532f1a
Create Date: 2018-03-19 17:17:59.110590

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "f17f0686ea6b"
down_revision = "adb4ea532f1a"
branch_labels = None
depends_on = None


def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_rdr():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index(
        "participant_summary_last_modified", "participant_summary", ["hpo_id", "last_modified"], unique=False
    )
    # ### end Alembic commands ###


def downgrade_rdr():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index("participant_summary_last_modified", table_name="participant_summary")
    # ### end Alembic commands ###


def upgrade_metrics():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade_metrics():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###