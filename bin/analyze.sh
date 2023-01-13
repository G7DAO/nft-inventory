#!/bin/bash

if [ ! "$1" ]; then
  echo "Contract must be given." 1>&2

  exit 0
fi

pnpm run analyze:static "$1"
pnpm run analyze:security "$1"