#!/bin/bash

MODE=$1

if [ $MODE = "b" ]; then
    docker build -t eng2sql -f "Dockerfile-EN" --label name=eng2sql .
fi

if [ $MODE = "r" ]; then
    docker run --name eng2sql --rm -p "127.0.0.1:8080:80" -p "127.0.0.1:8081:9001" eng2sql:latest
fi