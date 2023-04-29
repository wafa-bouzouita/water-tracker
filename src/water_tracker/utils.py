"""Useful tools."""

import json
from pathlib import Path


def load_dep_name_to_nb(ressource_path: Path) -> dict[str, str]:
    """Load departments json as  mapping from department name to number.

    Parameters
    ----------
    ressource_path : Path
        Path to the json file.

    Returns
    -------
    dict
        Mapping from department name to number.
    """
    depts_list: list[dict] = json.load(ressource_path.open(encoding="utf-8"))
    return {dpt["dep_name"]: dpt["num_dep"] for dpt in depts_list}
