#!/bin/bash
cd /opt/gigaknot/infinity
sudo service memcached start
python ./runfcgi.py runfcgi &