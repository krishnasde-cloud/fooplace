#!/usr/bin/env bash
set -euo pipefail

if ! docker info >/dev/null 2>&1; then
  sudo service docker start
  timeout 60 bash -c 'until docker info >/dev/null 2>&1; do sleep 1; done'
fi

docker compose up -d --wait
