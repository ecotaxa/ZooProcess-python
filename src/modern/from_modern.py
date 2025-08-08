from typing import List

from Models import Scan, ScanTypeEnum, SubSampleStateEnum
from ZooProcess_lib.ZooscanFolder import ZooscanProjectFolder
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
    if modern_fs.cut_dir.exists():
        ret = SubSampleStateEnum.SEGMENTED
    if modern_fs.MSK_validated_file_path.exists():
        ret = SubSampleStateEnum.MSK_APPROVED
    if modern_fs.multiples_vis_dir.exists():
        ret = SubSampleStateEnum.MULTIPLES_GENERATED
    return ret


def modern_scans_for_subsample(
    zoo_project: ZooscanProjectFolder,
    sample_name: str,
    subsample_name: str,
    modern_fs: ModernScanFileSystem,
) -> List[Scan]:
    msk_file = modern_fs.MSK_file_path()
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
