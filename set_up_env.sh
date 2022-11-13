PYTHON_PKG_DIR="./python_pkgs"

fail() {
    echo -en '\033[31mError: '
    echo $@
    echo "Installation has failed."
    echo -en '\033[0m'
    exit 1
}

which afl-showmap &>/dev/null || fail "Please install AFL or AFL++."
which python3 &>/dev/null || fail "Please install python3."
[ -n "$(ls $PYTHON_PKG_DIR/python-afl)" ] || fail "Looks like you're missing python-afl. Did you forget to clone this repository with \`--recurse-submodules\`?"

python3 -c 'import sys; exit(sys.prefix != sys.base_prefix)' || fail "Looks like you're already in a venv. This script needs to make its own venv. Please deactivate your venv and source this script again."

python3 -m venv url_fuzz_env || fail "Couldn't make a venv."
source ./url_fuzz_env/bin/activate || fail "Couldn't activate the venv."
pip3 install --upgrade pip || { deactivate; fail "Couldn't update pip."; }
for PKG in $PYTHON_PKG_DIR/*; do
    pip3 install "$PKG" || { deactivate; fail "Couldn't install $PKG."; }
done

echo -e "\033[32mYou are now in the fuzzing venv. run \`deactivate\` to exit the venv.\033[0m"
