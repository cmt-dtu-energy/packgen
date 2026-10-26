"""Command-line and parameters-file handling for the packing simulation."""

import json
import random
import sys
from collections.abc import Sequence
from pathlib import Path

DEFAULT_PARAMETERS_FILE = "parameters.json"


def get_parameters_file(argv: Sequence[str] | None = None) -> str:
    """Parse argument lists and return parameters file name.

    Args:
        argv: The argument list to parse. Defaults to `sys.argv`.
            The parameters file is the first argument after "--".

    """
    if argv is None:
        argv = sys.argv
    if "--" in argv:
        args = argv[list(argv).index("--") + 1 :]  # get all args after "--"
        if args:
            return args[0]
    return DEFAULT_PARAMETERS_FILE


def get_params_suffix(argv: Sequence[str] | None = None) -> str:
    """Get the base name of the parameters file without extension to use as a suffix.

    Args:
        argv: The argument list to parse. Defaults to `sys.argv`.

    Returns:
        str: The base name of the parameters file without extension.

    """
    return Path(get_parameters_file(argv)).stem


def load_parameters(
    parameters_file: str = DEFAULT_PARAMETERS_FILE,
) -> dict[str, float | bool]:
    """Load parameters from a JSON file.

    Args:
        parameters_file (str): Path to the parameters file.
            Defaults to "parameters.json".

    Returns:
        dict[str, float]: The loaded parameters mapping strings to float values.
            If 'seed' is null in the JSON, it will be converted to a random float.

    """
    with open(parameters_file) as f:
        params = json.load(f)
        if params.get("seed") is None:
            params["seed"] = random.random() * 1e6
        return params
