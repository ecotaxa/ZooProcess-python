from ZooProcess_lib.ZooscanFolder import ZooscanProjectFolder


def find_background_file(project: ZooscanProjectFolder, background_id: str):
    ret = project.zooscan_back.get_processed_background_file(background_id, 1)
    return ret
