"""Runs biobank samples pipeline, to develop metrics with full participants"""

import json
import logging

from rdr_service.main_util import configure_logging
from rdr_service.rdr_client.client import Client


def main():
    client = Client(base_path="offline")
    response = client.request_json("BiobankSamplesImport", "GET", cron=True)
    logging.info(json.dumps(response, indent=2, sort_keys=True))


if __name__ == "__main__":
    configure_logging()
    main()
