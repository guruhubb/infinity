#!/bin/bash
cd ~/code/gigaknot/infinity
git pull origin august
tools/stop.sh
tools/deploy.sh 
tools/start.sh
