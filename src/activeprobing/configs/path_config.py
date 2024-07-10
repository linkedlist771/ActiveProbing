import pathlib


ROOT_PATH = pathlib.Path(__file__).parent.parent.parent.parent
RESOURCES_DIR_PATH = ROOT_PATH / "resources"
RESOURCES_JSONS_DIR_PATH = RESOURCES_DIR_PATH / "jsons"
RESOURCES_IP_RANGES_DIR_PATH = RESOURCES_DIR_PATH / "ipranges"
RESOURCES_NMAP_SCAN_RES_DIR_PATH = RESOURCES_DIR_PATH / "nmap_scan_results"


if __name__ == "__main__":

    print(ROOT_PATH)
    print(RESOURCES_DIR_PATH)
    import os

    # check wheather it exists
    print(os.path.exists(RESOURCES_JSONS_DIR_PATH))
