#!/bin/sh

report_file() {
    file_path=$1
    printf '%s\n' "$file_path"
}

report_file "${1:-example with spaces}"
