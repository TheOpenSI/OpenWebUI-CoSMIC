# Step in container and check folder structure.
docker run -it open-webui /bin/bash

# Remove docker images.
docker rmi -f $(docker images -aq)

# Remove docker containers.
docker rm $(docker ps -aq)
docker rm $(docker ps -aq  --filter ancestor=opensi_docker)