#!/bin/bash

# Prepare box for joining
if [ "$1" == "-u" ]; then
	ad_user="$2"
	echo "user entered $ad_user"
else
	echo "user not entered"
fi

read -p "Press [ENTER] to run DOOM..."

# package installation
apt-get install -y realmd
apt-get install -y libnss-sss libpam-sss sssd sssd-tools adcli
apt-get install -y samba-common-bin oddjob oddjob-mkhomedir packagekit

# shut down AD
read -p "Press [ENTER] to configure resolv.conf..."
systemctl stop systemd-resolved.service
systemctl disable systemd-resolved.service

sed -i 's/^nameserver .*/nameserver 192.168.1.1/' /etc/resolv.conf

systemctl enable systemd-resolved.service
systemctl start systemd-resolved.service

cat /etc/resolv.conf

read -p "Press [ENTER] to join $ad_user to domain"

realm discover domain.net
realm join -U $ad_user domain.net

pam-auth-update

systemctl restart sssd

# Change hostname
echo "domain.net" > /etc/hostname

hostnamectl set-hostname $(cat /etc/hostname)

# Add group to `/etc/sudoers.d/domain_admins`, giving sudo permission on domain
touch /etc/sudoers.d/domain_admins
echo "%group@domain.net ALL=(ALL:ALL) ALL" > /etc/sudoers.d/domain_admins 2>/dev/null

read -p "Press [ENTER] to log onto domain"
su - $ad_user@domain.net
