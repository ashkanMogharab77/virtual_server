## Download and Run Setup Script

run the following commands:

```bash
apt update && apt upgrade -y
bash <(curl -Ls https://raw.githubusercontent.com/HamedAp/Ssh-User-management/master/install.sh --ipv4)
configure panel with shahan command
crontab -l | grep -vE '^\* +\* +\* +\* +\* +bash +/var/www/html/p/killusers\.sh.*$' | crontab -
reboot 

curl -O https://raw.githubusercontent.com/ashkanMogharab77/virtual_server/refs/heads/main/setup.sh
chmod +x setup.sh
./setup.sh
