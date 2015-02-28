#!/bin/bash
sudo cp ~/code/gigaknot/infinity/tools/nmsapp /etc/init.d
sudo chmod a+x /etc/init.d/nmsapp
sudo update-rc.d nmsapp defaults
sudo update-rc.d nmsapp enable
#done
