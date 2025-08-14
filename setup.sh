#!/bin/bash
set -e

echo "Starting prerequisite installation..."
apt install -y python3-venv at

echo "Checking and cloning git repository..."
git clone https://github.com/ashkanMogharab77/virtual_server.git

cd virtual_server
mv source /root
cd  
rm -r virtual_server
mv source virtual_server 
cd virtual_server
export $(xargs < .env)

echo "Setting password for mysql root user..."
mysql -u root <<EOF
ALTER USER 'root'@'localhost' IDENTIFIED BY '${DB_PASSWORD}';
FLUSH PRIVILEGES;
EOF

read -p "Server address : " ADDRESS
echo "Server address selected: $ADDRESS"

read -p "Telegram Token : " TOKEN
echo "Telegram Token selected: $TOKEN"

echo "ADDRESS=$ADDRESS" >> .env
echo "TOKEN=$TOKEN" >> .env

echo "Setting up block_duplicate_login.sh script..."
mv block_duplicate_login.sh /usr/local/bin/
chmod +x /usr/local/bin/block_duplicate_login.sh
sed -i '1i auth required pam_exec.so /usr/local/bin/block_duplicate_login.sh' /etc/pam.d/sshd

echo "Creating Python virtual environment and installing packages..."
python3 -m venv venv
venv/bin/pip install --no-cache-dir -r requirements

echo "Moving telegrambot service..."
mv telegrambot.service /etc/systemd/system/

echo "Allowing ports through ufw firewall..."
ufw enable
ufw allow $PORT
ufw allow 80
ufw allow 443

echo "Starting and enabling services..."
systemctl daemon-reexec
systemctl daemon-reload
systemctl start telegrambot.service
systemctl enable telegrambot.service
systemctl start atd
systemctl enable atd

echo "Setup completed."