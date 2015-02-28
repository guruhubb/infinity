#!/bin/bash
sudo service memcached stop
ps auxww | grep 'runfcgi' | awk '{print $2}' | xargs kill -9
