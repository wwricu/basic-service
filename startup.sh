#!/bin/bash                                                                                                            
docker run \
    -v `pwd`/static:/code/app/static \
    --net=host --restart=always \
    --name fastapi -d fastapi:latest
