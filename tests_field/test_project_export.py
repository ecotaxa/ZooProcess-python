import csv
import os
from datetime import datetime
from logging import getLogger
from pathlib import Path
from typing import List, Dict, Type, Iterator, Tuple

import numpy as np
import pytest

from Models import Sample, SubSample
from ZooProcess_lib.Features import BOX_MEASUREMENTS, TYPE_BY_LEGACY, TYPE_BY_ECOTAXA
from ZooProcess_lib.Processor import Processor
from ZooProcess_lib.ROI import ROI, ecotaxa_tsv_unq
from ZooProcess_lib.Segmenter import Segmenter
from ZooProcess_lib.ZooscanFolder import (
    ZooscanDrive,
    ZooscanProjectFolder,
    WRK_MEAS,
    WRK_TSV,
)

HERE = Path(__file__).parent

logger = getLogger(__name__)


def list_projects_and_sample() -> (
    Iterator[Tuple[ZooscanProjectFolder, Sample, SubSample]]
):
    """
    Generator yielding (zoo_project, sample, subsampe) for (sub)samples with legacy TSV export data
    """
    os.environ["APP_ENV"] = "dev"
    os.chdir(HERE.parent)
    import config_rdr
    from local_DB.db_dependencies import get_db
    from routers.projects import list_all_projects

    # Get the list of projects using the actual implementation
    projects = list_all_projects(next(get_db()), config_rdr.config.get_drives(), 3)

    for project in projects:
        zoo_project = ZooscanDrive(Path(project.drive.url)).get_project_folder(
            project.name
        )
        for sample in project.samples:
            for subsample in sample.subsample:
                work_files = zoo_project.zooscan_scan.work.get_files(
                    subsample.name, 1
                )  # Dig in Legacy work dir
                if WRK_TSV not in work_files or WRK_MEAS not in work_files:
                    continue
                yield zoo_project, sample, subsample


def to_object_keys(feat: Dict) -> Dict:
    out = {}
    for k, v in feat.items():
        out[f"object_{k.lower()}"] = v
    return out


def remove_object_features(rows: List[Dict]) -> None:
    """
    In-place removal of any keys starting with 'object_' from each dict in the list.
    This is used to ignore object_* fields when comparing TSV rows.
    """
    for row in rows:
        to_delete = [k for k in row.keys() if k.startswith("object_")]
        for k in to_delete:
            del row[k]


project_set = [(prj, sam, ssam) for (prj, sam, ssam) in list_projects_and_sample()]


@pytest.mark.parametrize(
    "zoo_project, sample, subsample",
    project_set,
    ids=[
        prj.path.name + ":" + subsample.name for (prj, sample, subsample) in project_set
    ],
)
def test_tsv_export_from_legacy_segmentation(
    zoo_project: ZooscanProjectFolder, sample: Sample, subsample: SubSample
):
    from modern.ids import scan_name_from_subsample_name
    from modern.jobs.VignettesToAutoSep import (
        get_scan_and_backgrounds,
    )
    from providers.ecotaxa_tsv import EcoTaxaTSV
    from providers.ecotaxa_tsv import TSV_HEADER

    scan_name = scan_name_from_subsample_name(subsample.name)
    processor = Processor.from_legacy_config(
        zoo_project.zooscan_config.read(),
        zoo_project.zooscan_config.read_lut(),
    )

    work_files = zoo_project.zooscan_scan.work.get_files(
        subsample.name, 1
    )  # Dig in Legacy work dir

    raw_scan, bg_scans = get_scan_and_backgrounds(logger, zoo_project, subsample.name)
    scan_resolution = 2400

    # Read legacy measures. NOT ALL features are present, but there is enough to sync comparison
    # of other fields.
    measures = work_files[WRK_MEAS]
    features = read_measures_from_file(measures)

    features = [to_object_keys(f) for f in features]

    # Generate fake ROIs with good size for vignette names
    rois = [
        ROI(
            feat["object_bx"],
            feat["object_by"],
            np.ndarray((feat["object_height"], feat["object_width"]), dtype=np.uint8),
        )
        for feat in features
    ]

    # Generate EcoTaxa data
    tsv_file_path = Path("/tmp") / (subsample.name + ".tsv")
    created_at = datetime.now()
    tsv_gen = EcoTaxaTSV(
        zoo_project,
        sample.name,
        subsample.name,
        scan_name,
        rois,
        features,
        created_at,
        scan_resolution,
        processor.segmenter,
        bg_scans,
    )
    tsv_types = TYPE_BY_ECOTAXA.copy()
    non_object_types = {k: str for k in TSV_HEADER if not k.startswith("object_")}
    tsv_types.update(non_object_types)

    tsv_gen.generate_into(tsv_file_path)
    generated_tsv = read_ecotaxa_tsv(tsv_file_path, typings=tsv_types)
    generated_tsv.sort(key=ecotaxa_tsv_unq)
    remove_object_features(generated_tsv)

    # Read Legacy generated TSV
    legacy_tsv = read_ecotaxa_tsv(work_files[WRK_TSV], typings=tsv_types)
    legacy_tsv.sort(key=ecotaxa_tsv_unq)
    remove_object_features(legacy_tsv)

    assert generated_tsv[0] == legacy_tsv[0]


# Dup code from lib tests TODO
def read_measures_from_file(measures, only_box=False):
    if only_box:
        ref = read_measures_csv(measures, BOX_MEASUREMENTS)
    else:
        ref = read_measures_csv(measures, TYPE_BY_LEGACY)
    # This filter is _after_ measurements in Legacy
    # TODO: Apparently it was not the case in projects before a certain date.
    ref = [
        a_ref
        for a_ref in ref
        if a_ref["Width"] / a_ref["Height"] < Segmenter.max_w_to_h_ratio
    ]
    sort_by_coords(ref)
    return ref


# Unicity inside a list of measures/features
feature_unq = lambda f: (f["BX"], f["BY"], f["Width"], f["Height"])


def sort_by_coords(features: List[Dict]):
    features.sort(key=feature_unq)


def read_box_measurements(
    project_folder: ZooscanProjectFolder, sample: str, index: int
) -> List[Dict]:
    work_files = project_folder.zooscan_scan.work.get_files(sample, index)
    measures = work_files[WRK_MEAS]
    ref = read_measures_from_file(measures, only_box=True)
    return ref


def read_measures_csv(csv_file: Path, typings: Dict[str, Type]) -> List[Dict]:
    ret = []
    with open(csv_file, "r") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for a_line in reader:
            to_add = {}
            for k, v in typings.items():
                if k in a_line:
                    typing = float if typings[k] == np.float64 else typings[k]
                    try:
                        to_add[k] = typing(a_line[k])
                    except ValueError as e:
                        # Some theoretically int features are stored as floats in CSVs
                        flt = float(a_line[k])
                        if int(flt) == flt:
                            to_add[k] = typing(flt)
            ret.append(to_add)
    return ret


def read_ecotaxa_tsv(
    csv_file: Path,
    typings: Dict[str, Type],
) -> List[Dict]:
    ret = []
    with open(csv_file, "r") as f:
        reader = csv.DictReader(f, delimiter="\t")
        first_line = True
        for a_line in reader:
            if first_line:
                first_line = False
                continue
            to_add = {}
            for k, v in typings.items():
                if k in a_line:
                    typing = float if typings[k] == np.float64 else typings[k]
                    try:
                        to_add[k] = typing(a_line[k])
                    except ValueError as e:
                        to_add[k] = None
                    # print("TSV: ", a_line[k], to_add[k])
            ret.append(to_add)
    return ret
