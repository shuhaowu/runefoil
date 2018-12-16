#!/bin/bash

set -xe

lxdock up
lxdock shell -c "runefoil-price restore"
lxdock shell -c "runefoil-price seed"
