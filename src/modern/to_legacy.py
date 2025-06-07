#
# Transformers from modern models to Legacy data
#
from typing import Optional, Dict, cast

from legacy.scans import ScanCSVLine


def reconstitute_fracid(fraction_id: str, fraction_id_suffix: Optional[str]) -> str:
    return fraction_id + ("_" + fraction_id_suffix if fraction_id_suffix else "")


def reconstitute_csv_line(scan_data: Dict) -> ScanCSVLine:
    ret = ScanCSVLine(**scan_data)  # type:ignore [typeddict-item]
    return cast(ScanCSVLine, ret)
