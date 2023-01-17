#!/bin/bash                                                                                                            
docker run \
    -v `pwd`/static:/fastapi/static \
    -v `pwd`/assets/production_config.json:/fastapi/assets/config.json \
    --net=host --restart=always --name fastapi -d fastapi:latest
