#!/bin/bash
set -e

if [ $# -ne 1 ]; then
  echo "Usage: $0 [name]"
  echo ''
  echo 'Options:'
  echo '  name              The RS256 public/private key pairs name.'
  exit 1
fi

NAME=$1
openssl genrsa -out "${NAME}_rsa_private.pem" 2048
openssl rsa -in "${NAME}_rsa_private.pem" -pubout -out "${NAME}_rsa_public.pem"
