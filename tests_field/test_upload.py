import logging
from logging import getLogger
from pathlib import Path

from providers.ecotaxa_client import EcoTaxaApiClient

HERE = Path(__file__).parent

ECOTAXA_SERVER = "https://ecotaxa.obs-vlfr.fr"
ECOTAXA_SERVER = "http://localhost:8000"
ZIP_FILE = Path("/tmp/tmpqkgi2yo1.zip")
EMAIL = "laurent.salinas@imev-mer.fr"
PASSWORD = "KYhtadRDPaBWv2B"
DST_PROJECT = 18068
DST_PROJECT = 16379

logger = getLogger(__name__)
logger.setLevel(logging.DEBUG)


def test_upload_and_import():
    """
    Login + my files upload
    """
    client = EcoTaxaApiClient(logger, ECOTAXA_SERVER, EMAIL, PASSWORD)
    client.open()
    logger.info(f"Connected as {client.whoami()}")
    # Upload the zip file
    remote_ref = client.put_file(ZIP_FILE, "/zpup/")
    logger.info(f"Zip file uploaded as {remote_ref}")
    # Start an import task with the file
    job_id = client.import_my_file_into_project(DST_PROJECT, "/zpup/")
    logger.info(f"Waiting for job {job_id}")
    final_job_state = client.wait_for_job_done(job_id)
    if final_job_state.state != "F":
        assert final_job_state.errors is not None
        assert False, "Job failed:" + "\n".join(final_job_state.errors)
