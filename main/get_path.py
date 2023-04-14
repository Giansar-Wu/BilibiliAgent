import os

ROOT_PATH = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
BIN_PATH = F"{ROOT_PATH}/bin"
MAIN_PATH = F"{ROOT_PATH}/main"
RESOURCE_PATH = F"{ROOT_PATH}/resources"

def print_path():
    print(F"ROOT_PATH:{ROOT_PATH}")
    print(F"BIN_PATH:{BIN_PATH}")
    print(F"MAIN_PATH:{MAIN_PATH}")
    print(F"RESOURCE_PATH:{RESOURCE_PATH}")

if __name__ == "__main__":
    print_path()