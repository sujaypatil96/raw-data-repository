"""add indexs for participant and ps

Revision ID: 58e8df756d74
Revises: edb6d45e5e45
Create Date: 2019-01-29 14:55:01.135611

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "58e8df756d74"
down_revision = "edb6d45e5e45"
branch_labels = None
depends_on = None


def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_rdr():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index("participant_sign_up_time", "participant", ["sign_up_time"], unique=False)
    op.create_index(
        "participant_summary_core_ordered_time",
        "participant_summary",
        ["enrollment_status_core_ordered_sample_time"],
        unique=False,
    )
    op.create_index(
        "participant_summary_core_stored_time",
        "participant_summary",
        ["enrollment_status_core_stored_sample_time"],
        unique=False,
    )
    op.create_index(
        "participant_summary_member_time", "participant_summary", ["enrollment_status_member_time"], unique=False
    )
    op.create_index("participant_summary_sign_up_time", "participant_summary", ["sign_up_time"], unique=False)
    # ### end Alembic commands ###


def downgrade_rdr():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index("participant_summary_sign_up_time", table_name="participant_summary")
    op.drop_index("participant_summary_member_time", table_name="participant_summary")
    op.drop_index("participant_summary_core_stored_time", table_name="participant_summary")
    op.drop_index("participant_summary_core_ordered_time", table_name="participant_summary")
    op.drop_index("participant_sign_up_time", table_name="participant")
    # ### end Alembic commands ###


def upgrade_metrics():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade_metrics():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###