#!/bin/bash
#BRANCH=$1
cd ~/code/gigaknot/infinity
#git pull origin $BRANCH
git pull origin master

# stop
ps auxww | grep 'runfcgi' | awk '{print $2}' | xargs kill -9

tools/deploy.sh

cd /opt/gigaknot/infinity
python ./runfcgi.py runfcgi &

