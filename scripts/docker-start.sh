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

if [ -f .env ]; then
  source .env
else
  DOT_RUNELITE_DIR=dot-runelite  # This is a docker managed volume
fi

docker-compose up -d "$@"
