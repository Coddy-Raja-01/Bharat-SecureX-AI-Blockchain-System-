#!/bin/sh
set -eu

test -n "${API_KEY:-}" || {
  echo "API_KEY must be configured for the frontend proxy" >&2
  exit 1
}

envsubst '${API_KEY}' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf