#!/bin/bash

set -xe

echo "{\"mysql_pw\": \"$(pwgen 10 1)\"}" > roles/runelite/vars/password.json
lxdock up
