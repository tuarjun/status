#!/bin/bash

while [ "meow" ]; do
    sleep 5m
    git pull
    git commit --allow-empty -m "Trigger Build"
    git push
done
