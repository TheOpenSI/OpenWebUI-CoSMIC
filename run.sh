#!/bin/bash

cd "$(dirname "$0")"
SCRIPT_DIR="$(pwd)"

image_name="open-webui"
container_name="open-webui"
host_port=3000
container_port=8080

docker build -t "$image_name" .
docker stop "$container_name" &>/dev/null || true
docker rm "$container_name" &>/dev/null || true

docker run -d -p "$host_port":"$container_port" \
    --add-host=host.docker.internal:host-gateway \
    -v "${image_name}:/app/backend/data" \
    --name "$container_name" \
    --restart always \
    --mount type=bind,source="${SCRIPT_DIR}/shared",target="/app/backend/shared" \
    --mount type=bind,source="${SCRIPT_DIR}/.env",target="/app/backend/.env" \
    "$image_name"

docker image prune -f

cd pipelines
bash start.sh
cd ..