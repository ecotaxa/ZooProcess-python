import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Union, Optional

from ZooProcess_lib.Extractor import Extractor
from ZooProcess_lib.Features import ECOTAXA_TSV_ROUNDINGS
from ZooProcess_lib.Legacy import averaged_median_mean
from ZooProcess_lib.ROI import ROI
from ZooProcess_lib.Segmenter import Segmenter
from ZooProcess_lib.ZooscanFolder import ZooscanProjectFolder
from ZooProcess_lib.img_tools import minAndMax, load_tiff_image_and_info
from legacy.samples import read_samples_metadata_table, find_sample_metadata
from legacy.scans import find_scan_metadata, read_scans_metadata_table
from modern.from_legacy import sample_from_legacy_meta
from modern.ids import THE_SCAN_PER_SUBSAMPLE
from modern.utils import extract_serial_number
from version import version_hash

SOFTWARE_FOR_TSVS = "zooprocess_10_0"


def get_hardware(scanner: Optional[str]) -> str:
    """Return Zooscan hardware generation from a scanner model using a lookup table."""
    if scanner is None:
        return "unknown"

    table = {
        # Others / not real zooscan
        "photosmart5520": "Other",
        "photosmart4870": "Other",
        # Not connected
        "no_scanner": "Zooscan_not_connected",
        # CNRS prototype
        "perfection2450": "CNRS_prototype",
        # Hydroptic versions
        "perfection4990": "Hydroptic_V1",
        "perfection4490": "Hydroptic_V2",
        # V3
        "perfectionv700": "Hydroptic_V3",
        "perfectionv750": "Hydroptic_V3",
        "gt-x900": "Hydroptic_V3",
        "gt-x970": "Hydroptic_V3",
        # V4
        "perfectionv800": "Hydroptic_V4",
        "perfectionv850": "Hydroptic_V4",
        "gt-x980": "Hydroptic_V4",
    }

    return table.get(scanner.lower(), "unknown")


LEGACY_COLUMNS = (
    # Refs
    "img_file_name,img_rank,object_id,object_link,"
    "object_lat,object_lon,object_date,object_time,object_depth_min,object_depth_max,object_lat_end,object_lon_end,"
    # Features
    "object_area,object_mean,object_stddev,object_mode,object_min,object_max,object_x,object_y,"
    # "object_xm,object_ym,"
    "object_perim.,object_bx,"
    "object_by,object_width,object_height,object_major,object_minor,object_angle,"
    "object_circ.,object_feret,object_intden,object_median,object_skew,object_kurt,"
    "object_%area,object_xstart,object_ystart,object_area_exc,object_fractal,"
    # "object_skelarea,object_slope,object_histcum1,object_histcum2,object_histcum3,object_xmg5,object_ymg5,"
    # "object_nb1,object_nb2,object_nb3,"
    # "object_compentropy,object_compmean,object_compslope,"
    # "object_compm1,object_compm2,object_compm3,"
    # "object_symetrieh,object_symetriev," # TODO See ClickUp
    # "object_symetriehc,object_symetrievc,object_convperim,"
    "object_convarea,"
    # "object_fcons,"
    # "object_thickr," # TODO See ClickUp
    # "object_tag,"
    "object_esd,object_elongation,object_range,object_meanpos,"
    # "object_centroids,"
    "object_cv,object_sr,"
    "object_perimareaexc,object_feretareaexc,object_perimferet,object_perimmajor,"
    "object_circex,"
    # "object_cdexc,"
    # Process
    "process_id,process_date,process_time,process_img_software_version,process_img_resolution,"
    "process_img_od_grey,process_img_od_std,"
    "process_img_background_img,process_particle_version,process_particle_threshold,process_particle_pixel_size_mm,"
    "process_particle_min_size_mm,process_particle_max_size_mm,"
    "process_particle_sep_mask,process_particle_bw_ratio,"
    "process_software,"
    # Acquisition
    "acq_id,acq_min_mesh,acq_max_mesh,acq_sub_part,acq_sub_method,acq_hardware,acq_software,acq_author,acq_imgtype,acq_scan_date,acq_scan_time,acq_quality,acq_bitpixel,acq_greyfrom,acq_scan_resolution,acq_rotation,acq_miror,acq_xsize,acq_ysize,acq_xoffset,acq_yoffset,acq_lut_color_balance,acq_lut_filter,acq_lut_min,acq_lut_max,acq_lut_odrange,acq_lut_ratio,acq_lut_16b_median,acq_instrument,acq_scan_comment,"
    # Sample
    "sample_id,sample_scan_operator,sample_ship,sample_program,sample_stationid,"
    "sample_bottomdepth,"
    "sample_ctdrosettefilename,sample_other_ref,"
    "sample_tow_nb,sample_tow_type,sample_net_type,sample_net_mesh,sample_net_surf,sample_zmax,"
    "sample_zmin,sample_tot_vol,sample_comment,sample_tot_vol_qc,sample_depth_qc,"
    "sample_sample_qc,sample_barcode,sample_duration,sample_ship_speed,sample_cable_length,"
    "sample_cable_angle,sample_cable_speed,sample_nb_jar,"
    "sample_dataportal_descriptor,sample_open"
)
TSV_HEADER = LEGACY_COLUMNS.rstrip(",").split(",")

LEGACY_EXCLUDED_COLUMNS = (
    # Refs
    # Features
    "object_xm,object_ym,"
    "object_skelarea,object_slope,object_histcum1,object_histcum2,object_histcum3,object_xmg5,object_ymg5,"
    "object_nb1,object_nb2,object_nb3,"
    "object_compentropy,object_compmean,object_compslope,"
    "object_compm1,object_compm2,object_compm3,"
    "object_symetrieh,object_symetriev,"  # TODO See ClickUp
    "object_symetriehc,object_symetrievc,object_convperim,"
    "object_fcons,"
    "object_thickr,"  # TODO See ClickUp
    "object_tag,"
    "object_centroids,"
    "object_cdexc,"
)


def round_for_tsv(feature: Dict[str, Any]) -> Dict[str, Any]:
    for k, v in feature.items():
        feature[k] = round(v, ECOTAXA_TSV_ROUNDINGS.get(k, 10))
    return feature


def float_or_int(value: Union[float, str]) -> Union[float, int]:
    ret = float(value)
    if float.is_integer(ret):
        return int(ret)
    return ret


def to_nan_if_nan(value: str) -> str:
    return "nan" if str(value) == "NaN" else value


class EcoTaxaTSV:
    """
    Data holder for ecotaxa TSV
    """

    def __init__(
        self,
        zoo_project: ZooscanProjectFolder,
        sample_name: str,
        subsample_name: str,
        scan_name: str,
        rois: List[ROI],
        features: List[Dict[str, Any]],
        start_date: datetime,
        resolution: int,
        segmenter: Segmenter,
        backgrounds: List[Path],
    ):
        self.zoo_project = zoo_project
        self.sample_name = sample_name
        self.subsample_name = subsample_name
        self.scan_name = scan_name
        self.rois = rois
        self.features = features
        self.start_date = start_date
        self.resolution = resolution
        self.segmenter = segmenter
        self.backgrounds = backgrounds
        assert len(self.rois) == len(self.features)
        assert len(self.rois) > 0
        all_samples_meta = read_samples_metadata_table(self.zoo_project)
        self.meta_for_sample = find_sample_metadata(all_samples_meta, self.sample_name)
        all_scans_meta = read_scans_metadata_table(self.zoo_project)
        self.meta_for_scan = find_scan_metadata(
            all_scans_meta, self.sample_name, self.scan_name
        )
        assert self.meta_for_sample is not None
        assert self.meta_for_scan is not None

    def generate_into(self, tsv_file_path: Path):
        tsv_refs = self.object_refs()
        tsv_geo = self.object_geo()
        tsv_sample = self.object_sample()
        tsv_acquisition = self.object_acquisition()
        tsv_process = self.object_process()
        headers = TSV_HEADER
        lines = [
            ref
            | round_for_tsv(feature)
            | tsv_geo
            | tsv_sample
            | tsv_acquisition
            | tsv_process
            for ref, feature in zip(tsv_refs, self.features)
        ]
        lines.sort(key=lambda l: (l["object_by"], l["object_bx"]))
        first_line = lines[0]
        types_line = {
            k: "[t]" if isinstance(v, str) else "[f]" for k, v in first_line.items()
        }

        assert set(types_line.keys()).issubset(TSV_HEADER)
        with open(tsv_file_path, "w") as f:
            writer = csv.DictWriter(f, fieldnames=headers, delimiter="\t")
            writer.writeheader()
            writer.writerow(types_line)
            for a_line in lines:
                writer.writerow(a_line)

    def object_refs(self) -> List[Dict[str, Any]]:
        rows = []
        for a_roi in self.rois:
            image_name = Extractor.vignette_name(a_roi, self.scan_name)
            rows.append(
                {
                    "img_file_name": image_name,
                    "img_rank": 0,
                    "object_id": image_name[:-4],
                    "object_link": "https://zenodo.org/records/14704251",
                }
            )
        return rows

    def object_geo(self) -> Dict[str, Any]:
        csv_datetime = self.meta_for_sample["date"]
        tsv_date, tsv_time = self.ini_date_to_tsv_date_and_time(csv_datetime)
        modern_meta = sample_from_legacy_meta(self.meta_for_sample)
        return {
            "object_lat": modern_meta["latitude_start"],
            "object_lon": modern_meta["longitude_start"],
            "object_date": tsv_date,
            "object_time": tsv_time,
            "object_depth_min": 0,
            "object_depth_max": self.meta_for_sample["depth"],
            "object_lat_end": modern_meta["latitude_end"],
            "object_lon_end": modern_meta["longitude_end"],
        }

    @classmethod
    def ini_date_to_tsv_date_and_time(cls, csv_datetime):
        tsv_date, tsv_time = csv_datetime.split("-")
        # 1200 -> 12:00:00.000
        tsv_time = tsv_time[:2] + ":" + tsv_time[2:] + ":00.000"
        return tsv_date, tsv_time

    @classmethod
    def scanlog_date_to_tsv_date_and_time(cls, csv_datetime):
        tsv_date, tsv_time = csv_datetime.split("_")
        # 20240529_1541 -> 20240529 15:41:00.000
        tsv_time = tsv_time[:2] + ":" + tsv_time[2:] + ":00.000"
        return tsv_date, tsv_time

    def object_sample(self) -> Dict[str, Any]:
        sample_meta = self.meta_for_sample
        scan_meta = self.meta_for_scan
        assert scan_meta is not None  # mypy
        return {
            "sample_id": self.sample_name,
            "sample_scan_operator": scan_meta["scanop"],
            "sample_ship": sample_meta["ship"],
            "sample_program": sample_meta["scientificprog"],
            "sample_stationid": sample_meta["stationid"],
            "sample_bottomdepth": sample_meta["depth"],
            "sample_ctdrosettefilename": sample_meta["ctdref"],
            "sample_other_ref": sample_meta["otherref"],
            "sample_tow_nb": int(sample_meta["townb"]),
            "sample_tow_type": sample_meta["towtype"],
            "sample_net_type": sample_meta["nettype"],
            "sample_net_mesh": float_or_int(sample_meta["netmesh"]),
            "sample_net_surf": float_or_int(sample_meta["netsurf"]),
            "sample_zmax": float_or_int(sample_meta["zmax"]),
            "sample_zmin": float_or_int(sample_meta["zmin"]),
            "sample_tot_vol": float_or_int(sample_meta["vol"]),
            "sample_comment": sample_meta["sample_comment"],
            "sample_tot_vol_qc": float_or_int(sample_meta["vol_qc"]),
            "sample_depth_qc": float_or_int(sample_meta["depth_qc"]),
            "sample_sample_qc": float_or_int(sample_meta["sample_qc"]),
            "sample_barcode": to_nan_if_nan(sample_meta["barcode"]),
            "sample_duration": float_or_int(sample_meta["net_duration"]),
            "sample_ship_speed": float_or_int(sample_meta["ship_speed_knots"]),
            "sample_cable_length": float_or_int(sample_meta["cable_length"]),
            "sample_cable_angle": float_or_int(sample_meta["cable_angle"]),
            "sample_cable_speed": float_or_int(sample_meta["cable_speed"]),
            "sample_nb_jar": float_or_int(sample_meta["nb_jar"]),
            "sample_dataportal_descriptor": "nan",
            "sample_open": "nan",
        }

    def object_acquisition(self) -> Dict[str, Any]:
        scan_csv_meta = self.meta_for_scan
        assert scan_csv_meta is not None  # mypy

        # Convert the scan to get measurements
        lut = self.zoo_project.zooscan_config.read_lut()
        raw_path = self.zoo_project.zooscan_scan.raw.get_file(
            self.subsample_name, THE_SCAN_PER_SUBSAMPLE
        )
        raw_info, raw_image = load_tiff_image_and_info(raw_path)
        median, _mean = averaged_median_mean(raw_image)
        min_rec, max_rec = minAndMax(median, lut)

        scan_log_meta = self.zoo_project.zooscan_scan.raw.get_scan_log(
            self.subsample_name, THE_SCAN_PER_SUBSAMPLE
        )
        assert scan_log_meta is not None, f"No _log for {self.scan_name} in {raw_path}"
        acq_date, acq_time = self.scanlog_date_to_tsv_date_and_time(
            scan_log_meta.scanning_date
        )
        acq_id = scan_csv_meta["fracid"] + "_" + self.sample_name
        zooscan_sn = extract_serial_number(self.zoo_project.path.name)
        if zooscan_sn.endswith("???"):
            zooscan_sn = "nan"
        return {
            "acq_id": acq_id,
            "acq_instrument": f"zooscan_{zooscan_sn}",  # zooscan serial number
            "acq_min_mesh": scan_csv_meta[
                "fracmin"
            ],  # minimum mesh size for the sieving of the scanned fraction of the sample [µm]
            "acq_max_mesh": scan_csv_meta[
                "fracsup"
            ],  # maximum mesh size for the sieving of the scanned fraction of the sample [µm]
            "acq_sub_part": scan_csv_meta[
                "fracnb"
            ],  # subsampling division factor of the sieved fraction of the sample
            "acq_sub_method": scan_csv_meta[
                "submethod"
            ],  # device utilized for the subsampling
            "acq_hardware": get_hardware(
                getattr(scan_log_meta, "scanner_source", "")
            ).lower(),  # zooscan model
            "acq_software": scan_log_meta.vuescan_version,  # scanning application and version
            "acq_author": scan_csv_meta["scanop"],  # image scanning operator
            "acq_imgtype": "zooscan",  # type of instrument utilized to scan the image
            "acq_scan_date": acq_date,  # date of the scan of the fraction [YYYYMMDD]
            "acq_scan_time": acq_time,  # time of the scan of the fraction [HHMMSS]
            "acq_quality": (
                "nan" if scan_log_meta.quality == -1 else scan_log_meta.quality
            ),  # scanned image quality index for scaning applications version before 9.7.67
            "acq_bitpixel": scan_log_meta.bits_per_pixel,  # 16 bits raw image coded grey scale
            "acq_greyfrom": scan_log_meta.make_gray_from,
            # index of the RGB chanel utilized to make the grey level image
            "acq_scan_resolution": scan_log_meta.scan_resolution,
            # resolution of the scanned image in dot per inch [dpi]
            "acq_rotation": scan_log_meta.rotation,  # rotation index to rotate the scanned image during the process
            "acq_miror": scan_log_meta.mirror,  # miror index to flip the scanned image during the process
            "acq_xsize": scan_log_meta.preview_x_size,  # width of the scanned image [pixel]
            "acq_ysize": scan_log_meta.preview_y_size,  # height of the scanned image [pixels]
            "acq_xoffset": scan_log_meta.preview_x_offset,  # x position of the scanned area [pixel]
            "acq_yoffset": scan_log_meta.preview_y_offset,  # y position of the scanned area [pixel]
            "acq_lut_color_balance": "manual",
            # type of conversion of the scanned 16 bit image to 8 bit image for the process (manual indicates that the zooprocess default method is utilized)
            "acq_lut_filter": lut.adjust,
            "acq_lut_min": min_rec,
            # zooprocess calculated black point for the 16 bits to 8 bit conversion of the scanned image
            "acq_lut_max": max_rec,
            # zooprocess calculated white point for the 16 bits to 8 bit conversion of the scanned image
            "acq_lut_odrange": lut.odrange,
            # optical density set range for the computing of the black point from the white point
            "acq_lut_ratio": lut.ratio,
            # multiplying factor to calculate the white point from the median grey level of the scanned image
            "acq_lut_16b_median": float_or_int(
                median
            ),  # median grey level of the scanned image
            "acq_scan_comment": scan_csv_meta["observation"],  #
        }

    def object_process(self) -> Dict[str, Any]:
        prc_id = f"zooprocess_{self.meta_for_sample["sampleid"]}"
        prc_date = self.start_date.strftime("%Y%m%d")
        prc_time = self.start_date.strftime("%H:%M:%S.000")
        pixel_size_mm = round(self.segmenter.pixel_size(self.resolution), 4)
        background_image = self.backgrounds[0].name.replace("_1.", ".")
        return {
            "process_id": prc_id,
            "process_date": prc_date,
            "process_time": prc_time,
            "process_img_software_version": version_hash(),
            "process_img_resolution": self.resolution,
            "process_img_od_grey": "",
            "process_img_od_std": "",
            "process_img_background_img": background_image,
            "process_particle_version": version_hash(),
            "process_particle_threshold": self.segmenter.threshold,
            "process_particle_pixel_size_mm": float_or_int(pixel_size_mm),
            "process_particle_min_size_mm": float_or_int(self.segmenter.minsize),
            "process_particle_max_size_mm": float_or_int(self.segmenter.maxsize),
            "process_particle_sep_mask": "include",
            "process_particle_bw_ratio": "",
            "process_software": SOFTWARE_FOR_TSVS,
        }
