import pickle
from typing import Any


def pickle_data(file_path: str, data: object) -> None:
    with open(file_path, "wb") as file:
        pickle.dump(data, file)


def get_pickled_data(file_path) -> Any:
    with open(file_path, "rb") as file:
        data = pickle.load(file)
    return data
