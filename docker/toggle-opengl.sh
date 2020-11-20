#!/bin/bash

p=shared/opengl-disabled

if [ -f $p ]; then
  echo -n "Currently OpenGL is disabled, enabling... "
  rm $p
  echo "enabled!"
else
  echo -n "Currently OpenGL is enabled, disabling... "
  touch $p
  echo "disabled!"
fi
