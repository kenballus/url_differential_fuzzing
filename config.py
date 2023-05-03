#############################################################################################
# config.py
# This is the configuration file for diff_fuzz.py
# Add new targets by adding new entries to TARGET_CONFIGS.
#############################################################################################

from pathlib import PosixPath
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
import os

# The directory where the seed inputs are
# The seeds are the files from which all the fuzzing inputs are produced,
# so it's important that the seeds are a decently representative sample
# of the inputs accepted by the targets.
SEED_DIR: PosixPath = PosixPath("./seeds")

# Where program traces end up
TRACE_DIR: PosixPath = PosixPath("./traces")

# Time in milliseconds given to each process
TIMEOUT_TIME: int = 10000

# Set this to false if you only care about exit status differentials
# (i.e. the programs you're testing aren't expected to have identical output on stdout)
OUTPUT_DIFFERENTIALS_MATTER: bool = True

# when this is True, a differential is registered if two targets exit with different status codes.
# When it's False, a differential is registered only when one target exits with status 0 and another
# exits with nonzero status.
EXIT_STATUSES_MATTER: bool = False

# Roughly how many processes to allow in a generation (within a factor of 2)
ROUGH_DESIRED_QUEUE_LEN: int = 1000


@dataclass
class TargetConfig:
    # The path to this target's executable
    executable: PosixPath
    # The CLI arguments this target needs
    cli_args: List[str] = field(default_factory=list)
    # Whether this executable should be traced.
    # (turning off tracing is useful for untraceable
    #  oracle targets, such as those written in
    #  unsupported languages)
    needs_tracing: bool = True
    # Whether this executable needs to run in QEMU mode
    # (should be True when target is not instrumented for AFL)
    needs_qemu: bool = False
    # Whether this executable needs to run with python-afl (is a python script)
    needs_python_afl: bool = False
    # The environment variables to pass to the executable
    env: Dict[str, str] = field(default_factory=lambda: dict(os.environ))


# Configuration for each fuzzing target
TARGET_CONFIGS: List[TargetConfig] = [
    TargetConfig(
        executable=PosixPath("./targets/urllib_target.py"),
        needs_python_afl=True,
    ),
    TargetConfig(
        executable=PosixPath("./targets/urllib3_target.py"),
        needs_python_afl=True,
    ),
    TargetConfig(
        executable=PosixPath("./targets/furl_target.py"),
        needs_python_afl=True,
    ),
    TargetConfig(
        executable=PosixPath("./targets/yarl_target.py"),
        needs_python_afl=True,
    ),
    TargetConfig(
        executable=PosixPath("./targets/rfc3986_target.py"),
        needs_python_afl=True,
    ),
    TargetConfig(
        executable=PosixPath("./targets/hyperlink_target.py"),
        needs_python_afl=True,
    ),
    TargetConfig(
        executable=PosixPath("./targets/curl/curl_target"),
    ),
    TargetConfig(
        executable=PosixPath("./targets/libwget/libwget_target"),
    ),
    TargetConfig(
        executable=PosixPath("./targets/boost_url/boost_url_target"),
    ),
]
