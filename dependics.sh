echo -e "\e[31mPlease start this script once. Don't disable your pc \e[39m"
sudo apt-get update
sudo apt install python3 python3-pip
pip3 install python-telegram-bot 
pip3 install mysql-connector-python
sudo apt install mysql-server
if [$? -ne 0]; then sudo apt install mariadb-server fi
sudo mysql_secure_installation
sudo mysql -u root -p -e " CREATE DATABASE bot; CREATE USER 'bot'@'localhost' IDENTIFIED BY 'sc8KCek9aaVf3Fnn'; "
sudo mysql -u root -p bot < bot.sql
sudo mysql -u root -p -e "GRANT ALL PRIVILEGES ON bot.* TO 'bot'@'localhost'; FLUSH PRIVILEGES;"
