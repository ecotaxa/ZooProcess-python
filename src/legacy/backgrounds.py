from ZooProcess_lib.ZooscanFolder import ZooscanProjectFolder


def find_final_background_file(project: ZooscanProjectFolder, background_date: str):
    ret = project.zooscan_back.get_processed_background_file(background_date, 1)
    return ret


def find_raw_background_file(
    project: ZooscanProjectFolder, background_date: str, index: str
):
    ret = project.zooscan_back.get_raw_background_file(background_date, index)
    return ret
