#!/bin/bash

DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_HOST=$DB_HOST
DB_NAME=$DB_NAME

if [[ $(uname) = "Darwin" ]]; then
  sed -i '' 's/'hippy'/'$DB_USER'/g' ./api-gtw-acck/handler.py
  sed -i '' 's/'pippy'/'$DB_PASSWORD'/g' ./api-gtw-acck/handler.py
  sed -i '' "s/=[[:space:]]'db'/= '$DB_HOST'/g" ./api-gtw-acck/handler.py
  sed -i '' 's/'yippy'/'$DB_NAME'/g' ./api-gtw-acck/handler.py
else
  sed -i'' 's/'hippy'/'$DB_USER'/g' ./api-gtw-acck/handler.py
  sed -i'' 's/'pippy'/'$DB_PASSWORD'/g' ./api-gtw-acck/handler.py
  sed -i'' "s/=\s'db'/= '$DB_HOST'/g" ./api-gtw-acck/handler.py
  sed -i'' 's/'yippy'/'$DB_NAME'/g' ./api-gtw-acck/handler.py
fi