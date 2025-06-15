#!/bin/env bash

find . -type f -name "*.py" \
    -not -path "*/node_modules/*" \
    -not -path "*/__pycache__/*" \
    -not -path "*/.venv/*" \
    -exec sh -c 'expand --tabs=4 "$1" > "$1.tmp" && mv "$1.tmp" "$1"' _ {} \;
