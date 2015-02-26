#!/bin/bash

echo "Cleaning up existing deployment."
rm -Rf /opt/gigaknot
mkdir -p /opt/gigaknot
mkdir -p /opt/log

echo "Deploying Nginx Configuration"
sudo cp ~/code/gigaknot/infinity/nginx/nginx.conf /etc/nginx
sudo cp ~/code/gigaknot/infinity/nginx/nms.nginx /etc/nginx/sites-available/nms
sudo ln -sf /etc/nginx/sites-available/nms /etc/nginx/sites-enabled/nms

echo "Deploying Flask app"
cp -r ~/code/gigaknot/infinity /opt/gigaknot

echo "Explode static content"
cd /opt/gigaknot/infinity

#echo "Deploying Cron Jobs"
#crontab -r
#crontab -l | { cat; echo "* * * * *  export NMS_PROFILE=$PROFILE python; /opt/nms/infinity/cron_alerts.py"; } | crontab -
#sudo service cron restart
