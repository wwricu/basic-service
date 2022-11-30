#!/bin/bash                                                                                                            
docker run \
    --net=host --restart=always \
    --name fastapi -d fastapi:latest
