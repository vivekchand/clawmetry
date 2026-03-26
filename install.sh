#!/bin/bash
set -e

curl -L https://git.new/get-ipm | bash

if [ -r /dev/tty ] 2>/dev/null; then
  ipm i vivekchand/clawmetry < /dev/tty
else
  ipm i vivekchand/clawmetry
fi
