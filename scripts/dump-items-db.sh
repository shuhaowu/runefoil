#!/bin/bash

lxdock shell -c "mysqldump runelite prices items" | gzip > runefoil/files/items-prices-db-dump.sql.gz
