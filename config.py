#############################################################################################
# config.py
# This is the configuration file for diff_fuzz.py
# Add new targets by adding new entries to TARGET_CONFIGS.
#############################################################################################

from pathlib import PosixPath
from typing import List, Dict, Tuple
from dataclasses import dataclass, field
from os import environ

# The directory where the seed inputs are
# The seeds are the files from which all the fuzzing inputs are produced,
# so it's important that the seeds are a decently representative sample
# of the inputs accepted by the targets.
SEED_DIR: PosixPath = PosixPath("./seeds")

# The directory where the findings go when the fuzzer run finishes.
RESULTS_DIR: PosixPath = PosixPath("./results")

# The directory the fuzzer saves inputs into
EXECUTION_DIR: PosixPath = PosixPath("./execution")

# Time in milliseconds given to each process
TIMEOUT_TIME: int = 10000

# Set this to False if you only care about exit status differentials
# (i.e. the programs you're testing aren't expected to have identical output on stdout)
DETECT_OUTPUT_DIFFERENTIALS: bool = True

# Set this to True if you want to use grammar mutations.
# (Requires a grammar.py with the appropriate interface)
USE_GRAMMAR_MUTATIONS: bool = True

# When this is True, a differential is registered if two targets exit with different status codes.
# When it's False, a differential is registered only when one target exits with status 0 and another
# exits with nonzero status.
DIFFERENTIATE_NONZERO_EXIT_STATUSES: bool = False

# Roughly how many processes to allow in a generation (within a factor of 2)
ROUGH_DESIRED_QUEUE_LEN: int = 100

# The number of bytes deleted at a time in the minimization loop
# The default choice was selected because of UTF-8.
DELETION_LENGTHS: List[int] = [4, 3, 2, 1]


# This is the parse tree class for your programs' output.
# If DETECT_OUTPUT_DIFFERENTIALS is set to False, then you can leave this as it is.
# Otherwise, it should have a `bytes` field for each field in your programs'
# output JSON.
@dataclass(frozen=True)
class ParseTree:
    scheme: bytes
    host: bytes
    path: bytes
    port: bytes
    query: bytes
    userinfo: bytes
    fragment: bytes


# This is the comparison operation on optional parse trees.
# During minimization, the result of the function is preserved.
# If your programs' output is expected to match completely, then leave this as-is.
# Otherwise, rewrite it to implement an equivalence operation between your parse trees.
def compare_parse_trees(t1: ParseTree | None, t2: ParseTree | None) -> Tuple[bool, ...]:
    return (t1 is t2,) if t1 is None or t2 is None else (
        t1.scheme == t2.scheme,
        t1.host == t2.host,
        t1.path == t2.path or all(path in (b"", b"/") for path in (t1.path, t2.path)),
        t1.port == t2.port,
        t1.query == t2.query,
        t1.userinfo == t2.userinfo,
        t1.fragment == t2.fragment,
    )


# This is the configuration class for each target program.
@dataclass(frozen=True)
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
    env: Dict[str, str] = field(default_factory=lambda: dict(environ))


# Configuration for each fuzzing target
TARGET_CONFIGS: List[TargetConfig] = [
    # TargetConfig(
    #     executable=PosixPath("./targets/boost_url/boost_url_target"),
    # ),
    # TargetConfig(
    #     executable=PosixPath("./targets/curl/curl_target"),
    # ),
    TargetConfig(
        executable=PosixPath("./targets/furl/furl_target"),
        needs_python_afl=True,
    ),
    TargetConfig(
        executable=PosixPath("./targets/hyperlink/hyperlink_target"),
        needs_python_afl=True,
    ),
    # TargetConfig(
    #     executable=PosixPath("./targets/libwget/libwget_target"),
    # ),
    TargetConfig(
        executable=PosixPath("./targets/rfc3986/rfc3986_target"),
        needs_python_afl=True,
    ),
    TargetConfig(
        executable=PosixPath("./targets/urllib/urllib_target"),
        needs_python_afl=True,
    ),
    TargetConfig(
        executable=PosixPath("./targets/urllib3/urllib3_target"),
        needs_python_afl=True,
    ),
    TargetConfig(
        executable=PosixPath("./targets/yarl/yarl_target"),
        needs_python_afl=True,
    ),
]
