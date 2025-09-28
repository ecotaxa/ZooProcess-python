from typing import List

from Models import Scan, ScanTypeEnum, SubSampleStateEnum
from ZooProcess_lib.ZooscanFolder import ZooscanProjectFolder
from helpers.paths import file_date, count_files_in_dir
from modern.app_urls import generate_work_image_url
from modern.filesystem import ModernScanFileSystem
from modern.ids import (
    hash_from_project,
    hash_from_sample_name,
    hash_from_subsample_name,
    THE_SCAN_PER_SUBSAMPLE,
)
from modern.users import SYSTEM_USER


def modern_facet_of_subsample(
    zoo_project: ZooscanProjectFolder, sample_name: str, subsample_name: str
) -> tuple[SubSampleStateEnum, list[Scan]]:
    modern_fs = ModernScanFileSystem(zoo_project, sample_name, subsample_name)
    # Add modern unique scan files
    return (
        modern_subsample_state(zoo_project, sample_name, subsample_name, modern_fs),
        modern_scans_for_subsample(zoo_project, sample_name, subsample_name, modern_fs),
    )


def modern_subsample_state(
    zoo_project: ZooscanProjectFolder,
    sample_name: str,
    subsample_name: str,
    modern_fs: ModernScanFileSystem,
) -> SubSampleStateEnum:
    ret = SubSampleStateEnum.EMPTY
    raw_scan = zoo_project.zooscan_scan.raw.get_file(
        subsample_name, THE_SCAN_PER_SUBSAMPLE
    )
    if raw_scan.exists():
        ret = SubSampleStateEnum.ACQUIRED

    msk_file_path = modern_fs.MSK_file_path
    scores_file_path = modern_fs.scores_file_path
    if ret == SubSampleStateEnum.ACQUIRED:
        scan_date = file_date(
            raw_scan
        )  # TODO: Maybe use get_creation_date which reads TIF but it's very slow
        cut_dir = modern_fs.cut_dir
        if (
            cut_dir.exists()
            and msk_file_path.exists()
            and file_date(msk_file_path) > scan_date
        ):
            if scores_file_path.exists():
                ret = SubSampleStateEnum.SEGMENTED
            else:
                ret = SubSampleStateEnum.SEGMENTATION_FAILED

    if ret == SubSampleStateEnum.SEGMENTED:
        valid_msk = modern_fs.MSK_validated_file_path
        if valid_msk.exists() and (file_date(valid_msk) > file_date(msk_file_path)):
            ret = SubSampleStateEnum.MSK_APPROVED

    multiples_dir = modern_fs.multiples_vis_dir
    if ret == SubSampleStateEnum.MSK_APPROVED:
        if multiples_dir.exists() and count_files_in_dir(multiples_dir) >= 0:
            if modern_fs.SEP_generated_file_path.exists():
                ret = SubSampleStateEnum.MULTIPLES_GENERATED
            else:
                ret = SubSampleStateEnum.MULTIPLES_GENERATION_FAILED

    separation_approved = modern_fs.SEP_validated_file_path
    if ret == SubSampleStateEnum.MULTIPLES_GENERATED:
        if separation_approved.exists():
            ret = SubSampleStateEnum.SEPARATION_VALIDATION_DONE

    upload_done = modern_fs.upload_done_path
    upload_zip = modern_fs.zip_for_upload
    if ret == SubSampleStateEnum.SEPARATION_VALIDATION_DONE:
        if upload_zip.exists():
            if upload_done.exists():
                ret = SubSampleStateEnum.UPLOADED
            else:
                ret = SubSampleStateEnum.UPLOAD_FAILED

    return ret


def modern_scans_for_subsample(
    zoo_project: ZooscanProjectFolder,
    sample_name: str,
    subsample_name: str,
    modern_fs: ModernScanFileSystem,
) -> List[Scan]:
    msk_file = modern_fs.MSK_file_path
    if msk_file.exists():
        project_hash = hash_from_project(zoo_project.path)
        sample_hash = hash_from_sample_name(sample_name)
        subsample_hash = hash_from_subsample_name(subsample_name)
        scan = Scan(
            id=msk_file.name,
            url=generate_work_image_url(
                project_hash, sample_hash, subsample_hash, msk_file.name, True
            ),
            type=ScanTypeEnum.V10_MASK,
            user=SYSTEM_USER,
        )
        return [scan]
    return []
