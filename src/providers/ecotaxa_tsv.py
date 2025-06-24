import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from ZooProcess_lib.Extractor import Extractor
from ZooProcess_lib.Features import ECOTAXA_TSV_ROUNDINGS
from ZooProcess_lib.ROI import ROI
from ZooProcess_lib.Segmenter import Segmenter
from ZooProcess_lib.ZooscanFolder import ZooscanProjectFolder
from legacy.samples import read_samples_metadata_table, find_sample_metadata
from legacy.scans import find_scan_metadata, read_scans_metadata_table
from modern.from_legacy import sample_from_legacy_meta
from version import version_hash

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
    # "process_img_od_grey,process_img_od_std,"
    "process_img_background_img,process_particle_version,process_particle_threshold,process_particle_pixel_size_mm,"
    "process_particle_min_size_mm,process_particle_max_size_mm,"
    # "process_particle_sep_mask,process_particle_bw_ratio,"
    "process_software,"
    # Sample
    "sample_id,sample_scan_operator,sample_ship,sample_program,sample_stationid,"
    "sample_bottomdepth,"
    # "sample_ctdrosettefilename,sample_other_ref,"
    "sample_tow_nb,sample_tow_type,sample_net_type,sample_net_mesh,sample_net_surf,sample_zmax,"
    "sample_zmin,sample_tot_vol,sample_comment,sample_tot_vol_qc,sample_depth_qc,"
    "sample_sample_qc,sample_barcode,sample_duration,sample_ship_speed,sample_cable_length,"
    "sample_cable_angle,sample_cable_speed,sample_nb_jar,"
    # "sample_dataportal_descriptor,sample_open"
)
TSV_HEADER = LEGACY_COLUMNS.rstrip(",").split(",")


def round_for_tsv(feature: Dict[str, Any]) -> Dict[str, Any]:
    for k, v in feature.items():
        feature[k] = round(v, ECOTAXA_TSV_ROUNDINGS.get(k, 10))
    return feature


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
        tsv_process = self.object_process()
        tsv_sample = self.object_sample()
        headers = TSV_HEADER
        lines = [
            ref | round_for_tsv(feature) | tsv_geo | tsv_process | tsv_sample
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
                    "object_link": "http://www.zooscan.obs-vlfr.fr/",
                }
            )
        return rows

    def object_geo(self) -> Dict[str, Any]:
        csv_datetime = self.meta_for_sample["date"]
        tsv_date, tsv_time = csv_datetime.split("-")
        # 1200 -> 12:00:00.000
        tsv_time = tsv_time[:2] + ":" + tsv_time[2:] + ":00.000"
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

    def object_process(self) -> Dict[str, Any]:
        prc_id = f"zooprocess_{self.meta_for_sample["sampleid"]}"
        prc_date = self.start_date.strftime("%y%m%d")
        prc_time = self.start_date.strftime("%H:%M:%S.000")
        pixel_size_mm = round(self.segmenter.pixel_size(self.resolution), 4)
        background_image = self.backgrounds[0].name.replace("_1.", ".")
        return {
            "process_id": prc_id,
            "process_date": prc_date,
            "process_time": prc_time,
            "process_img_software_version": version_hash(),
            "process_img_resolution": self.resolution,
            # "process_img_od_grey": "",
            # "process_img_od_std": "",
            "process_img_background_img": background_image,
            "process_particle_version": version_hash(),
            "process_particle_threshold": self.segmenter.threshold,
            "process_particle_pixel_size_mm": pixel_size_mm,
            "process_particle_min_size_mm": self.segmenter.minsize,
            "process_particle_max_size_mm": self.segmenter.maxsize,
            # "process_particle_sep_mask": "",
            # "process_particle_bw_ratio": "",
            "process_software": "ZooProcess v10",
        }

    def object_sample(self) -> Dict[str, Any]:
        sample_meta = self.meta_for_sample
        scan_meta = self.meta_for_scan
        return {
            "sample_id": sample_meta["sampleid"],
            "sample_scan_operator": scan_meta["scanop"],
            "sample_ship": sample_meta["ship"],
            "sample_program": sample_meta["scientificprog"],
            "sample_stationid": sample_meta["stationid"],
            "sample_bottomdepth": sample_meta["depth"],
            # "sample_ctdrosettefilename": "",
            # "sample_other_ref": "",
            "sample_tow_nb": int(sample_meta["townb"]),
            "sample_tow_type": sample_meta["towtype"],
            "sample_net_type": sample_meta["nettype"],
            "sample_net_mesh": float(sample_meta["netmesh"]),
            "sample_net_surf": float(sample_meta["netsurf"]),
            "sample_zmax": float(sample_meta["zmax"]),
            "sample_zmin": float(sample_meta["zmin"]),
            "sample_tot_vol": float(sample_meta["vol"]),
            "sample_comment": sample_meta["sample_comment"],
            "sample_tot_vol_qc": float(sample_meta["vol_qc"]),
            "sample_depth_qc": float(sample_meta["depth_qc"]),
            "sample_sample_qc": float(sample_meta["sample_qc"]),
            "sample_barcode": sample_meta["barcode"],
            "sample_duration": float(sample_meta["net_duration"]),
            "sample_ship_speed": float(sample_meta["ship_speed_knots"]),
            "sample_cable_length": float(sample_meta["cable_length"]),
            "sample_cable_angle": float(sample_meta["cable_angle"]),
            "sample_cable_speed": float(sample_meta["cable_speed"]),
            "sample_nb_jar": float(sample_meta["nb_jar"]),
            # "sample_dataportal_descriptor": "",
            # "sample_open": "",
        }
