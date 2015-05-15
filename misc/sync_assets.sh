#!/bin/bash
if [ $(pidof -x $(basename $0)| wc -w) -gt 2 ]; then
    basename $0
    exit
else
    RC=1
    while [[ RC -ne 0 ]]
    do
        rsync --delete -d -d -e "ssh -o StrictHostKeyChecking=no" $1@yustplayit.com:~/assets/* /home/pi/yustplayit_assets/
        RC=$?
        sleep 300
    done
fi

