import time
from logging import Logger
from pathlib import Path
from typing import IO, cast

from urllib3.exceptions import HTTPWarning

from .EcoTaxa.ecotaxa_model import *
from .EcoTaxa.simple_client import SimpleClient


class EcoTaxaApiClient(SimpleClient):
    """
    An API client wrapper class for Ecotaxa.
    """

    def __init__(self, logger: Logger, url: str, email: str, password: str):
        super().__init__(url)
        self.logger = logger
        self.email = email
        self.password = password

    @classmethod
    def from_token(cls, logger: Logger, url: str, token: str) -> "EcoTaxaApiClient":
        ret = cls(logger, url, "", "")
        ret.token = token
        return ret

    def open(self):
        """
        Open a connection to the API by logging in.
        """
        token = self.login()
        assert token is not None, "Auth failed!"
        self.token: str = token

    def login(self):
        self.logger.info(f"Logging in to EcoTaxa at {self.base_url}")
        req = LoginReq(username=self.email, password=self.password)
        try:
            rsp = self.post(str, "/login", json=req)
        except HTTPWarning:
            return None
        return rsp

    def whoami(self) -> UserModelWithRights:
        """
        Example API call for fetching own name.
        """
        rsp: UserModelWithRights = self.get(UserModelWithRights, "/users/me")
        return rsp

    def wait_for_job_done(self, job_id: int) -> JobModel:
        self.logger.info("Waiting for job #%d", job_id)
        while True:
            try:
                rsp: JobModel = self.get(JobModel, "/jobs/%d/" % job_id)
            except ConnectionError:
                time.sleep(10)
                continue
            if rsp.state in ("E", "F"):  # Final states: Error or Finished
                return rsp
            time.sleep(10)

    def get_task_file(self, job_id: int):
        rsp = self.get(IO, "/jobs/%d/file" % job_id, stream=False)
        return rsp

    def export_project(self, exp_req):
        req = {"filters": {}, "request": exp_req}
        job_id = self.post(int, "/object_set/export", json=req)
        return job_id

    def import_FTP_into_project(self, dst_prj, exp_file_path):
        req = {
            "source_path": "/FTP/Ecotaxa_Exported_data/%s" % exp_file_path,
            "skip_existing_objects": True,
        }
        job_id = self.post(int, "/file_import/%d" % dst_prj, json=req)
        return job_id

    def list_acquisitions(self, prj_id: int):
        rsp: List[AcquisitionModel] = self.get(
            List[AcquisitionModel], "/acquisitions/search?project_id=%d" % prj_id
        )
        return rsp

    def list_zooscan_projects(self) -> List[ProjectModel]:
        rsp: List[ProjectModel] = self.get(
            List[ProjectModel], "/projects/search?instrument_filter=Zooscan"
        )
        return rsp

    def update_acquisitions(self, acquis_ids: List[int], field: str, val: str) -> int:
        req = {"target_ids": acquis_ids, "updates": [{"ucol": field, "uval": val}]}
        rsp: int = self.post(int, "/acquisition_set/update", json=req)
        return rsp

    def query_object_set(
        self, prj: int, order: str, disp_cols: List[str], status: Optional[str] = None
    ) -> List[ObjectModel]:
        # std gui ones
        flds = "obj.objid%2Cobj.classif_qual%2Cobj.imgcount%2Cobj.complement_info%2Cimg.height%2Cimg.width%2Cimg.thumb_file_name%2Cimg.thumb_height%2Cimg.thumb_width%2Cimg.file_name%2Ctxo.name%2Ctxo.display_name"
        if disp_cols:
            flds += "%2C".join([""] + disp_cols)
        pag_from = 0
        pag_size = 200
        filters = {}
        if status:
            filters["statusfilter"] = status
        qry = f"/object_set/{prj}/query?fields={flds}&order_field={order}&window_start={pag_from}&window_size={pag_size}"
        rsp = self.post(ObjectSetQueryRsp, qry, json=filters)
        return cast(List[ObjectModel], rsp)

    def query_acquisition_object_set(
        self, prj: int, sample_id: int, acq_id: int, disp_cols=None
    ) -> List[Dict]:
        if disp_cols is None:
            disp_cols = []
        flds = "obj.objid%2Cobj.orig_id%2Cobj.acquisid"
        if disp_cols:
            flds += "%2C".join([""] + disp_cols)
        filters = {"samples": sample_id}
        qry = f"/object_set/{prj}/query?fields={flds}"
        rsp = self.post(ObjectSetQueryRsp, qry, json=filters)
        # e.g. [990827551, 'apero2023_tha_bioness_sup2000_013_st46_d_n4_d2_1_sur_1_1_x2BD2y36Ew204h17C', 10557563]
        rsp_for_acq = [
            dict(objid=objid, orig_id=orig_id, acquisid=acquisid)
            for objid, orig_id, acquisid in rsp.details
            if acquisid == acq_id  # Filter manually
        ]
        return rsp_for_acq

    def put_file(self, zip_file: Path, remote_dir: str) -> str:
        with open(zip_file, "rb") as fin:
            upload_rsp = self.post(
                str,
                "/user_files/",
                files={"file": fin},
                data={"path": remote_dir + "/" + zip_file.name},
            )
            return cast(str, upload_rsp)

    def import_my_file_into_project(
        self,
        dst_prj_id: int,
        my_file_path: str,
        skip_existing_objects: bool = False,
        update_mode: str = "",
    ) -> int:
        req = {
            "source_path": my_file_path,
            "skip_existing_objects": skip_existing_objects,
            "update_mode": update_mode,
        }
        job_status: ImportRsp = self.post(
            ImportRsp, "/file_import/%d" % dst_prj_id, json=req
        )
        assert job_status.errors is not None, "No error list returned!"
        assert len(job_status.errors) == 0, job_status.errors
        return job_status.job_id
