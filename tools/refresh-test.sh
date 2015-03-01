#!/bin/bash
cd ~/code/gigaknot/infinity
git pull origin master
tools/stop.sh
tools/deploy.sh 
tools/start.sh
