#!/bin/bash

export JAVA_HOME=$(dirname $(dirname $(readlink -f `which java`)))
echo $JAVA_HOME

sed -i "s/PORT/$PORT/g" /etc/nginx/sites-enabled/default
supervisord -n
