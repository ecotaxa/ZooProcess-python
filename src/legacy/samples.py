from typing import List, TypedDict


class SampleCSVLine(TypedDict):
    """TypedDict representing the structure of a sample CSV record."""

    sampleid: str  # Unique identifier for the sample (e.g., 'apero2023_tha_bioness_sup2000_017_st66_d_n1')
    ship: str  # Name of the ship (e.g., 'thalassa')
    scientificprog: str  # Scientific program name (e.g., 'apero')
    stationid: str  # Station identifier (e.g., '66')
    date: str  # Sampling date in format YYYYMMDD-HHMM (e.g., '20230704-0503')
    latitude: (
        str  # Starting latitude in degrees-minutes format, converted to decimal degrees
    )
    longitude: str  # Starting longitude in degrees-minutes format, converted to decimal degrees
    depth: str  # Bottom depth in meters (e.g., '99999')
    ctdref: str  # CTD reference (e.g., 'apero_bio_ctd_017')
    otherref: str  # Other reference (e.g., 'apero_bio_uvp6_017u')
    townb: str  # Number of tow (e.g., '1')
    towtype: str  # Tow type (e.g., '1')
    nettype: str  # Net sampling type (e.g., 'bioness')
    netmesh: str  # Net mesh size in microns (e.g., '2000')
    netsurf: str  # Net opening surface (e.g., '1')
    zmax: str  # Maximum depth in meters (e.g., '1008')
    zmin: str  # Minimum depth in meters (e.g., '820')
    vol: str  # Volume (e.g., '357')
    sample_comment: str  # Comments about the sample
    vol_qc: str  # Quality flag for volume (e.g., '1')
    depth_qc: str  # Quality flag for depth measurement (e.g., '1')
    sample_qc: str  # Quality flag for sample (e.g., '1111')
    barcode: str  # Barcode (e.g., 'ape000000147')
    latitude_end: (
        str  # Ending latitude in degrees-minutes format, converted to decimal degrees
    )
    longitude_end: (
        str  # Ending longitude in degrees-minutes format, converted to decimal degrees
    )
    net_duration: str  # Sampling duration in minutes (e.g., '20')
    ship_speed_knots: str  # Ship speed in knots (e.g., '2')
    cable_length: str  # Cable length in meters (e.g., '9999')
    cable_angle: str  # Cable angle from vertical in degrees (e.g., '99999')
    cable_speed: str  # Cable speed (e.g., '0')
    nb_jar: str  # Number of jars (e.g., '1')


def find_sample_metadata(all_sample_metadata: List[SampleCSVLine], sample_name: str):
    for a_sample_meta in all_sample_metadata:
        if a_sample_meta["sampleid"] == sample_name:
            return a_sample_meta
    return None
