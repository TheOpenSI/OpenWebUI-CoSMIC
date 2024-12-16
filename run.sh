#!/bin/bash

cd "$(dirname "$0")"
SCRIPT_DIR="$(pwd)"

image_name="open-webui"
container_name="open-webui"
host_port=3000
container_port=8080

cp ${SCRIPT_DIR}/backend/open_webui/apps/cosmic/config.yaml ${SCRIPT_DIR}/shared/config_updated.yaml

docker build -t "$image_name" .
docker stop "$container_name" &>/dev/null || true
docker rm "$container_name" &>/dev/null || true

docker run -d -p "$host_port":"$container_port" \
    --add-host=host.docker.internal:host-gateway \
    -v "${image_name}:/app/backend/data" \
    --name "$container_name" \
    --restart always \
    --mount type=bind,source="${SCRIPT_DIR}/shared",target="/app/backend/shared" \
    "$image_name"

docker image prune -f

cd pipelines
bash start.sh
cd ..