#!/bin/bash

set -xe

nft -f /etc/nftables.conf

exec /usr/local/bin/docker-entrypoint.sh "$@"
