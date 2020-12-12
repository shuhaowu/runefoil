#!/bin/bash

if [ "$1" == "-f" ]; then
  docker-compose exec main rm -f /opt/runelite/lock
fi

docker-compose exec main /opt/runefoil/bin/runefoil
