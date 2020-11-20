#!/bin/bash

echo $1 > shared/gdk-scale

echo "Current GDK_SCALE is $(cat shared/gdk-scale)"

if [ "$1" == "1" ]; then
  rm -f shared/gdk-scale # Remove the file if GDK_SCALE is normal.
fi
