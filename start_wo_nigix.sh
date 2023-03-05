#!/usr/bin/env bash

PROJECT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)

docker build -t chatgpt/server $PROJECT_DIR

docker run --name chatgpt-web -dp 80:3002 --env_file $PROJECT_DIR/openai.env chatgpt/server:latest
