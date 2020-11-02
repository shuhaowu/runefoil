#!/bin/bash


set -xe

export UID
export GID=$(id -g)
docker-compose up -d
