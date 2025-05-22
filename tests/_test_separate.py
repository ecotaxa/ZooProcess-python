from helpers.debug_tools import dump_structure
from img_tools import mkdir
from separate_fn import separate_images

userhome = "/Users/sebastiengalvagno/"
piqv = "piqv/plankton/zooscan_monitoring/"
piqvhome = userhome + piqv
project = "Zooscan_dyfamed_wp2_2023_biotom_sn001/Zooscan_scan/_work/dyfamed_20230111_100m_d1_1/multiples_to_separate/"
file = "dyfamed_20230111_100m_d1_1_309.jpg"
# file = "dyfamed_20230111_100m_d1_1_454.jpg"
path = piqvhome + project  # +file
zooscan_mask_folder = project + "mask/"
zooscan_result_folder = project + "result/"


# def mkdir(path):
#     from pathlib import Path
#     Path(path).mkdir(parents=True, exist_ok=True)


def _test_separate():
    mkdir(zooscan_mask_folder)
    mkdir(zooscan_result_folder)
    images = separate_images(
        path=path,
        path_out=zooscan_mask_folder,
        path_result=zooscan_result_folder,
        db=None,
    )

    dump_structure(images)

    # def _test_separate_images(self):

    #     img_src = path + file
    #     # file_dst =
    #     img_dst = zooscan_result_folder + file

    #     file_mask = 'dyfamed_20230111_100m_d1_1_309_mask.png'
    #     mask = zooscan_mask_folder + file_mask

    #     print("mask: ", mask)

    #     # exit()
    #     mkdir(zooscan_result_folder)
    #     img = separate_apply_mask(img_src,mask)

    #     # src = "/Users/sebastiengalvagno/piqv/plankton/zooscan_monitoring/Zooscan_dyfamed_wp2_2023_biotom_sn001/Zooscan_scan/_work/dyfamed_20230111_100m_d1_1/multiples_to_separate/dyfamed_20230111_100m_d1_1_453.jpg"
    #     # mask_src="Zooscan_dyfamed_wp2_2023_biotom_sn001/Zooscan_scan/_work/dyfamed_20230111_100m_d1_1/multiples_to_separate/mask/dyfamed_20230111_100m_d1_1_453_mask.png"
    #     # img = separate_apply_mask(src,mask_src)

    #     saveimage(img,img_dst)
    #     print("image merged: ", img_dst)


def test_image_to_public():

    mkdir(zooscan_mask_folder)
    dest = "/Users/sebastiengalvagno/Work/test/nextui/zooprocess_v10/public/separated/"
    mkdir(dest)

    images = separate_images(
        path=path, path_out=zooscan_mask_folder, path_result=dest, taskId=None
    )

    dump_structure(images)
