#!/bin/bash

docker build -t timelapser .
docker-compose stop timelapser
docker-compose up -d timelapser
