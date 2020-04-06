#! /bin/env python
#
# Template for RDR tool python program.
#

import argparse

# pylint: disable=superfluous-parens
# pylint: disable=broad-except
import logging
import os
import sys

from rdr_service.dao.participant_dao import ParticipantDao
from rdr_service.model.biobank_stored_sample import BiobankStoredSample
from rdr_service.model.measurements import PhysicalMeasurements
from rdr_service.model.participant import Participant
from rdr_service.model.biobank_order import BiobankOrder, BiobankOrderIdentifier

from rdr_service.services.system_utils import setup_logging, setup_i18n
from rdr_service.tools.tool_libs import GCPProcessContext, GCPEnvConfigObject

_logger = logging.getLogger("rdr_logger")

# Tool_cmd and tool_desc name are required.
# Remember to add/update bash completion in 'tool_lib/tools.bash'
tool_cmd = "fix-dup-pids"
tool_desc = "Fix duplicated participants"


class ProgramTemplateClass(object):
    def __init__(self, args, gcp_env: GCPEnvConfigObject):
        """
        :param args: command line arguments.
        :param gcp_env: gcp environment information, see: gcp_initialize().
        """
        self.args = args
        self.gcp_env = gcp_env

    def get_participant_records(self, dao, pids):
        """
        Return the participant records for each pid in pids.
        :param dao: DAO object to run queries with.
        :param pids: Tuple with 3 pid values.
        :return: Original Participant record, New Participant 1 record, New Participant 2 record.
        """
        with dao.session() as session:
            p = session.query(Participant).filter(Participant.participantId == pids[0]).first()
            p1 = session.query(Participant).filter(Participant.participantId == pids[1]).first()
            p2 = session.query(Participant).filter(Participant.participantId == pids[2]).first()

        return p, p1, p2

    def get_biobank_records_for_participant(self, dao, mappings):
        """
        Return the participant, biobank order, and stored sample records mappings.
        :param dao: DAO object to run queries with.
        :param mappings: Tuple with old_pid, new_pid, biobank_order_id.
        :return: old participant, new participant,
        biobank order, stored sample records
        """
        with dao.session() as session:
            op = session.query(Participant).filter(Participant.participantId == mappings[0]).first()
            np = session.query(Participant).filter(Participant.participantId == mappings[1]).first()
            bbo = session.query(BiobankOrder).filter(BiobankOrder.biobankOrderId == mappings[2]).first()
            ss = session.query(BiobankStoredSample).join(
                BiobankOrderIdentifier,
                BiobankOrderIdentifier.value == BiobankStoredSample.biobankOrderIdentifier
            ).filter(
                BiobankOrderIdentifier.biobankOrderId == mappings[2]
            ).all()

        return op, np, bbo, ss

    def get_pm_records_for_participant(self, dao, mappings):
        """
       Return the physical measurement and participant records in mappings.
       :param dao: DAO object to run queries with.
       :param mappings: Tuple with old_pid, new_pid, and pm_id.
       :return: old participant, new participant, and pm records
       """
        with dao.session() as session:
            op = session.query(Participant).filter(Participant.participantId == mappings[0]).first()
            np = session.query(Participant).filter(Participant.participantId == mappings[1]).first()
            pm = session.query(PhysicalMeasurements).filter(
                PhysicalMeasurements.physicalMeasurementsId == mappings[2]
            ).first()
        return op, np, pm

    def fix_biobank_order(self, dao, np, bbo):
        """
        Updates the Biobank Order object to the new PID
        :param dao: the dao
        :param np: new participant
        :param bbo: biobank order object
        :return: updated biobank order object
        """
        bbo.participantId = np.participantId
        with dao.session() as session:
            return session.merge(bbo)

    def fix_biobank_stored_sample(self, dao, np, ss):
        """
        Updates the Biobank stored sample to the new biobank_id
        :param dao:
        :param np: new participant
        :param ss: stored sample object
        :return: updated sample object
        """
        ss.biobankId = np.biobankId
        with dao.session() as session:
            return session.merge(ss)

    def fix_pm(self, dao, op, np, pm):
        """
        Updates the Physical Measurement object to the new PID
        :param dao: the dao
        :param np: new participant
        :param pm: physical measurement object
        :return: updated physical measurment object
        """
        pid_strings = (str(op.participantId), str(np.participantId))
        pm.participantId = np.participantId
        # Update the resource request with the correct PID
        for entry in pm.resource['entry']:
            new_ref = entry['resource']['subject']['reference'].replace(*pid_strings)
            entry['resource']['subject']['reference'] = new_ref
        with dao.session() as session:
            return session.merge(pm)

    def run(self):
        """
        Main program process
        :return: Exit code value
        """

        """
        Example: Enabling colors in terminals.
            Using colors in terminal output is supported by using the self.gcp_env.terminal_colors
            object.  Errors and Warnings are automatically set to Red and Yellow respectively.
            The terminal_colors object has many predefined colors, but custom colors may be used
            as well. See rdr_service/services/TerminalColors for more information.
        """
        # clr = self.gcp_env.terminal_colors
        # _logger.info(clr.fmt('This is a blue info line.', clr.fg_bright_blue))
        # _logger.info(clr.fmt('This is a custom color line', clr.custom_fg_color(156)))

        self.gcp_env.activate_sql_proxy()
        dao = ParticipantDao()

        mappings_list = list()

        if self.args.participant:
            mappings_list.append(tuple(i.strip() for i in self.args.participant.split(',')))
        else:
            with open(self.args.csv, encoding='utf-8-sig') as h:
                lines = h.readlines()
                for line in lines:
                    mappings_list.append(tuple(i.strip() for i in line.split(',')))
                if self.args.fix_biobank_orders:
                    headers = mappings_list.pop(0)
                    if headers != ("old_pid", "new_pid", "biobank_order_id"):
                        _logger.error("Invalid columns in CSV")
                        _logger.error(f"   {headers}")
                        return 1

                if self.args.fix_physical_measurements:
                    headers = mappings_list.pop(0)
                    if headers != ("old_pid", "new_pid", "pm_id"):
                        _logger.error("Invalid columns in CSV")
                        _logger.error(f"   {headers}")
                        return 1

        if self.args.fix_biobank_orders:
            for mapping in mappings_list:
                old_p, new_p, biobank_order, stored_samples = self.get_biobank_records_for_participant(dao, mapping)

                if not old_p or not new_p or not biobank_order or not stored_samples:
                    _logger.error(
                        f'  error {old_p.participantId}, {new_p.participantId}, {biobank_order.biobankOrderId}')
                    continue

                # Process Biobank Orders
                _logger.warning(
                    f'  reassigning Biobank Order {biobank_order.biobankOrderId} | '
                    f'{old_p.participantId} -> {new_p.participantId}')
                updated_bbo = self.fix_biobank_order(dao, new_p, biobank_order)
                _logger.info(f'  update successful for {updated_bbo.biobankOrderId}: '
                             f'{updated_bbo.participantId}')

                # Process Biobank Stored Samples
                for sample in stored_samples:
                    _logger.warning(
                        f'  reassigning Stored Sample {sample.biobankStoredSampleId} | '
                        f'{old_p.biobankId} -> {new_p.biobankId}')
                    updated_ss = self.fix_biobank_stored_sample(dao, new_p, sample)
                    _logger.info(f'  update successful for {updated_ss.biobankStoredSampleId}: '
                                 f'{updated_ss.biobankId}')

        if self.args.fix_physical_measurements:
            for mapping in mappings_list:
                old_p, new_p, physical_measurement = self.get_pm_records_for_participant(dao, mapping)

                if not old_p or not new_p or not physical_measurement:
                    _logger.error(
                        f'  error {old_p.participantId}, '
                        f'{new_p.participantId}, '
                        f'{physical_measurement.physicalMeasurementsId}')
                    continue

                # Process Physical Measurement
                _logger.warning(
                    f'  reassigning Physical Measurement {physical_measurement.physicalMeasurementsId} | '
                    f'{old_p.participantId} -> {new_p.participantId}')
                updated_pm = self.fix_pm(dao, old_p, new_p, physical_measurement)
                _logger.info(f'  update successful for PM ID {updated_pm.physicalMeasurementsId}: '
                             f'{updated_pm.participantId}')

        return 0


def run():
    # Set global debug value and setup application logging.
    setup_logging(
        _logger, tool_cmd, "--debug" in sys.argv, "{0}.log".format(tool_cmd) if "--log-file" in sys.argv else None
    )
    setup_i18n()

    # Setup program arguments.
    parser = argparse.ArgumentParser(prog=tool_cmd, description=tool_desc)
    parser.add_argument("--debug", help="enable debug output", default=False, action="store_true")  # noqa
    parser.add_argument("--log-file", help="write output to a log file", default=False, action="store_true")  # noqa
    parser.add_argument("--project", help="gcp project name", default="localhost")  # noqa
    parser.add_argument("--account", help="pmi-ops account", default=None)  # noqa
    parser.add_argument("--service-account", help="gcp iam service account", default=None)  # noqa
    parser.add_argument("--csv", help="csv file with participant ids", default=None)  # noqa
    parser.add_argument("--participant", help="old pid,new pid 1,new pid 2", default=None)  # noqa
    parser.add_argument("--fix-biobank-orders", help="Fix Biobank Orders", default=False, action="store_true")  # noqa
    parser.add_argument("--fix-physical-measurements", help="Fix Physical Measurements",
                        default=False, action="store_true")  # noqa
    args = parser.parse_args()

    if not args.fix_biobank_orders and not args.fix_physical_measurements:
        _logger.error('Either --fix-biobank-orders or --fix-physical-measurements must be provided.')
        return 1

    if args.fix_biobank_orders and args.fix_physical_measurements:
        _logger.error('Arguments --fix_biobank_orders and --fix_physical_measurements may not be used together.')
        return 1

    if not args.participant and not args.csv:
        _logger.error('Either --csv or --participant argument must be provided.')
        return 1

    if args.participant and args.csv:
        _logger.error('Arguments --csv and --participant may not be used together.')
        return 1

    if args.participant:
        # Verify that we have a string with 3 comma delimited values.
        if len(args.participant.split(',')) != 3:
            _logger.error('Invalid participant argument, must be 3 PIDs in comma delimited format.')
            return 1

    if args.csv:
        if not os.path.exists(args.csv):
            _logger.error(f'File {args.csv} was not found.')
            return 1

    with GCPProcessContext(tool_cmd, args.project, args.account, args.service_account) as gcp_env:
        process = ProgramTemplateClass(args, gcp_env)
        exit_code = process.run()
        return exit_code


# --- Main Program Call ---
if __name__ == "__main__":
    sys.exit(run())