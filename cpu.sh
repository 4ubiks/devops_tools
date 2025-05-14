#!/bin/bash

# colors
RED="\e[31m"
GREEN="\e[92m"
CYAN="\e[36m"
WHITE="\e[97m"
BOLDWHITE="\e[1;${WHITE}"
BOLDGREEN="\e[1;${GREEN}"
BOLDRED="\e[1;${RED}"
ENDCOLOR="\e[0m"

# other constants
border="================================================"
echo -e '\n'
# os
os=$(lsb_release -d | awk '{print $2, $3, $4}')
echo -e ${BOLDGREEN}$os${ENDCOLOR}

echo -e ${BOLDWHITE}$border${ENDCOLOR}

# uptime
currDate=$(date | awk '{print $2, $3, $6}')
currTime=$(date | awk '{print $4}')
currUp=$(awk '{print int($1/3600)":"int(($1%3600)/60)":"int($1%60)}' /proc/uptime)

echo -e 'Date/Time:' ${BOLDWHITE}$currDate, $currTime${ENDCOLOR}
echo -e 'CPU uptime:' ${BOLDWHITE}$currUp${ENDCOLOR} '\n'
echo -e ${BOLDWHITE}$border${ENDCOLOR}

# usage
cpuCurr=$(grep 'cpu ' /proc/stat | awk '{usage=($2+$4)*100/($2+$4+$5)} END {print usage "%"}')
echo -e 'usage' ${BOLDRED}$cpuCurr${ENDCOLOR} '\n'
echo -e ${BOLDWHITE}$border${ENDCOLOR}

# ram
echo -e 'memory'
memTotal=$(free -h | grep 'Mem:' | awk '{print $2}')
memUsed=$(free -h | grep 'Mem:' | awk '{print $3}')
memFree=$(free -h | grep 'Mem:' | awk '{print $4}')

echo -e "Total memory:" ${BOLDWHITE}$memTotal${ENDCOLOR}
echo -e "Used memory:" ${BOLDRED}$memUsed${ENDCOLOR} 
echo -e "Free memory:" ${BOLDGREEN}$memFree${ENDCOLOR} '\n'

echo -e ${BOLDWHITE}$border${ENDCOLOR}

# five intensive processes
echo -e 'five intensive processses' '\n'
echo -e ${BOLDWHITE}$border${ENDCOLOR}

# temp
echo -e 'idk what this is' '\n'
echo -e ${BOLDWHITE}$border${ENDCOLOR}

# cpu specs
echo -e 'CPU Information'
arch=$(lscpu | grep Architecture | awk '{print $2}')
order=$(lscpu | grep 'Byte Order' | awk '{print $3, $4}')
echo -e $arch, $order '\n'
