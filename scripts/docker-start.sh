#!/bin/bash


set -xe

export UID
export GID=$(id -g)

pushd shared
if [ ! -d runelite/.git ]; then
  echo "Runelite not available, cloning..."
  git clone https://github.com/runelite/runelite.git
fi
popd

docker-compose up -d "$@"
