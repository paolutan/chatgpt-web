SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
PROJECT_DIR=$SCRIPT_DIR

set -e
pip3 install virtualenv
python3 -m virtualenv $PROJECT_DIR/.venv
$PROJECT_DIR/.venv/bin/python -m pip install --upgrade pip

$PROJECT_DIR/.venv/bin/pip install -r $PROJECT_DIR/requirements.txt
