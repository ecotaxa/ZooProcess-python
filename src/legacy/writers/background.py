# Set of files in legacy filesystem:
#     From scanning software:
#         20210624_0852_back_large_raw_1.tif
#         20210624_0852_back_large_raw_2.tif
#     Intermediate:
#         20210624_0852_back_large_1.tif
#         20210624_0852_back_large_2.tif
#     Final:
#         20210624_0852_background_large_manual.tif
#     Log file (INI-like with settings):
#         20210624_0852_back_large_manual_log.txt


def file_name_for_raw_background(timestamp: str, frame_num: int) -> str:
    return f"{timestamp}_back_large_raw_{frame_num}.tif"
