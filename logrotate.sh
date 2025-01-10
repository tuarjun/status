#!/bin/bash

folder="logs"
for file in "$folder"/*; do
    if [[ -f "$file" ]]; then
        tail -n 1000 "$file" > "$file""
    fi
done
