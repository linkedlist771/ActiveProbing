import pathlib


ROOT_PATH = pathlib.Path(__file__).parent.parent.parent.parent
RESOURCES_DIR_PATH = ROOT_PATH / "resources"
RESOURCES_JSONS_DIR_PATH = RESOURCES_DIR_PATH / "jsons"


if __name__ == "__main__":

    print(ROOT_PATH)
    print(RESOURCES_DIR_PATH)
    import os
    # check wheather it exists
    print(os.path.exists(RESOURCES_JSONS_DIR_PATH))