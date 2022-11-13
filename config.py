#############################################################################################
# config.py
# This is the configuration file for diff_fuzz.py
# Add new targets by adding new entries to TARGET_CONFIGS.
#############################################################################################

from pathlib import PosixPath
from typing import NamedTuple
import os

# The directory where the seed inputs are
SEED_DIR: PosixPath = PosixPath("./seeds")

# Where program traces end up
TRACE_DIR: PosixPath = PosixPath("./traces")

# Time in milliseconds given to each process
TIMEOUT_TIME: int = 100000

# Roughly how many processes to allow in a generation (within a factor of 2)
ROUGH_DESIRED_QUEUE_LEN: int = 1000

class TargetConfig(NamedTuple):
    executable: PosixPath  # The path to this target's executable
    cli_args: List[str]  # The CLI arguments this target needs
    needs_qemu: bool  # Whether this executable needs to run in QEMU mode (is a binary that wasn't compiled with afl-cc)
    needs_python_afl: bool  # Whether this executable needs to run with python-afl (is a python script)
    env: Dict[str, str]  # The environment variables to pass to the executable


# Configuration for each fuzzing target
TARGET_CONFIGS: List[TargetConfig] = [
    TargetConfig(
        executable=PosixPath("./targets/cpython_urllib_target.py"),
        cli_args=[],
        needs_qemu=False,
        needs_python_afl=True,
        env=dict(os.environ),
    ),
    TargetConfig(
        executable=PosixPath("./targets/whatwg_url_target.py"),
        cli_args=[],
        needs_qemu=False,
        needs_python_afl=True,
        env=dict(os.environ),
    ),
    TargetConfig(
        executable=PosixPath("./targets/urllib3_target.py"),
        cli_args=[],
        needs_qemu=False,
        needs_python_afl=True,
        env=dict(os.environ),
    ),
    TargetConfig(
        executable=PosixPath("./targets/rfc3986_target.py"),
        cli_args=[],
        needs_qemu=False,
        needs_python_afl=True,
        env=dict(os.environ),
    ),
    TargetConfig(
        executable=PosixPath("./targets/rfc3987_target.py"),
        cli_args=[],
        needs_qemu=False,
        needs_python_afl=True,
        env=dict(os.environ),
    ),
    # TargetConfig(
    #    executable=PosixPath("./targets/curl/build/src/curl"),
    #    cli_args=[],
    #    needs_qemu=False,
    #    needs_python_afl=False,
    #    env=dict(os.environ),
    # ),
    # TargetConfig(
    #    executable=PosixPath("./targets/wget2/src/.libs/wget2"),
    #    cli_args=[],
    #    needs_qemu=False,
    #    needs_python_afl=False,
    #    env=dict(os.environ) | {"LD_LIBRARY_PATH": "/home/bkallus/fuzzing/url_fuzzing/targets/wget2/libwget/.libs/"},
    # ),
]
