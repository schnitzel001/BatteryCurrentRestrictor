#!/bin/bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
kill $(pgrep -f "python $SCRIPT_DIR/battery_current_restrictor.py")