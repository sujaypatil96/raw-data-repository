# pylint: disable=superfluous-parens
import json
import logging
import os
import time
import traceback
import random

from rdr_service.config import GoogleCloudDatastoreConfigProvider
from rdr_service.services.gcp_utils import gcp_activate_sql_proxy, gcp_cleanup, gcp_initialize, gcp_format_sql_instance
from rdr_service.services.system_utils import remove_pidfile, write_pidfile_or_die, git_project_root

_logger = logging.getLogger("rdr_logger")


class GCPEnvConfigObject(object):
    """ GCP environment configuration object """

    _sql_proxy_process = None

    project = None
    git_project = None

    def __init__(self, items):
        """
        :param items: dict of config key value pairs
        """
        for key, val in items.items():
            self.__dict__[key] = val

        # Determine the git project root directory.
        envron_path = os.environ.get('RDR_PROJECT', None)
        git_root_path = git_project_root()
        if envron_path:
            self.git_project = envron_path
        elif git_root_path:
            self.git_project = git_root_path
        else:
            _logger.warning("GCPEnvConfigObject: no git project root found.")

    def cleanup(self):
        """ Clean up or close everything we need to """
        if self._sql_proxy_process:
            self._sql_proxy_process.terminate()

    def get_app_config(self):
        """
        Get the application config.
        :return: dict
        """
        # https://github.com/googleapis/google-auth-library-python/issues/271
        import warnings
        warnings.filterwarnings("ignore", "Your application has authenticated using end user credentials")

        provider = GoogleCloudDatastoreConfigProvider()
        # See if we should use local configs or cloud configs.
        if not self.project or self.project == 'localhost':
            file = os.path.join(self.git_project, 'rdr_service/.configs/current_config.json')
            config = json.loads(open(file, 'r').read())
        else:
            config = provider.load('current_config', project=self.project)

        return config

    def get_app_db_config(self):
        """
        Get the application database config.
        :return: dict
        """
        # https://github.com/googleapis/google-auth-library-python/issues/271
        import warnings
        warnings.filterwarnings("ignore", "Your application has authenticated using end user credentials")

        provider = GoogleCloudDatastoreConfigProvider()
        if not self.project or self.project == 'localhost':
            file = os.path.join(self.git_project, 'rdr_service/.configs/db_config.json')
            config = json.loads(open(file, 'r').read())
        else:
            config = provider.load('db_config', project=self.project)

        return config

    def activate_sql_proxy(self, user: str = 'rdr', project: str = None, replica: bool = False):
        """
        Activate a google sql proxy instance service and set DB_CONNECTION_STRING environment var.
        :param user: database user, must be one of ['root', 'alembic', 'rdr'].
        :param project: GCP project id.
        :param replica: Use replica db instance or Primary instance.
        :return: pid
        """
        if self._sql_proxy_process:
            self._sql_proxy_process.terminate()
            self._sql_proxy_process = None

        db_config = self.get_app_db_config()

        # If localhost project, just point to the local instance of mysql.
        if (project and project == 'localhost') or (self.project and self.project == 'localhost'):
            passwd = 'root' if user == 'root' else 'rdr!pwd'
            os.environ['DB_CONNECTION_STRING'] = f'mysql+mysqldb://{user}:{passwd}@127.0.0.1:3306/rdr?charset=utf8'
            return 1

        _logger.debug("Starting google sql proxy...")
        port = random.randint(10000, 65535)

        instance = gcp_format_sql_instance(project if project else self.project, port=port, replica=replica)
        self._sql_proxy_process = gcp_activate_sql_proxy(instance)

        if self._sql_proxy_process:
            time.sleep(6)  # allow time for sql connection to be made.
            cfg_user = 'root' if user == 'root' else 'rdr'
            passwd = db_config[f'{cfg_user}_db_password']
            os.environ['DB_CONNECTION_STRING'] = f'mysql+mysqldb://{user}:{passwd}@127.0.0.1:{port}/rdr?charset=utf8'
            return self._sql_proxy_process.pid

        _logger.error('Failed to activate sql proxy.')

        return 0


class GCPProcessContext(object):
    """
  A processing context manager for GCP operations
  """

    _command = None
    _project = None
    _account = None
    _service_account = None
    _env = None

    _env_config_obj = None

    def __init__(self, command, project, account=None, service_account=None):
        """
    Initialize GCP Context Manager
    :param command: command name
    :param project: gcp project name
    :param account: pmi-ops account
    :param service_account: gcp iam service account
    """
        if not command:
            _logger.error("command not set, aborting.")
            exit(1)

        self._command = command
        self._project = project
        self._account = account
        self._service_account = service_account

        write_pidfile_or_die(command)
        self._env = gcp_initialize(project, account, service_account)
        if not self._env:
            remove_pidfile(command)
            exit(1)

    def __enter__(self):
        """ Return object with properties set to config values """
        self._env_config_obj = GCPEnvConfigObject(self._env)
        return self._env_config_obj

    def __exit__(self, exc_type, exc_val, exc_tb):
        """ Clean up or close everything we need to """
        self._env_config_obj.cleanup()
        gcp_cleanup(self._account)
        remove_pidfile(self._command)

        if exc_type is not None:
            print((traceback.format_exc()))
            _logger.error("program encountered an unexpected error, quitting.")
            exit(1)