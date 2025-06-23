#!/usr/bin/env bash
# -----------------------------------------------------------------------------
#
# Licensed Materials - Property of IBM
# 5697-DA7
# (C) Copyright IBM Corp. 2022, 2023.
#
# US Government Users Restricted Rights
# Use, duplication or disclosure restricted by GSA ADP Schedule
# Contract with IBM Corp.
#
# DISCLAIMER OF WARRANTIES :
#
# Permission is granted to copy and modify this  Sample code provided
# that both the copyright  notice,- and this permission notice and
# warranty disclaimer  appear in all copies and modified versions.
#
# THIS SAMPLE CODE IS LICENSED TO YOU AS-IS.
# IBM  AND ITS SUPPLIERS AND LICENSORS  DISCLAIM ALL WARRANTIES,
# EITHER EXPRESS OR IMPLIED, IN SUCH SAMPLE CODE, INCLUDING THE
# WARRANTY OF NON-INFRINGEMENT AND THE IMPLIED WARRANTIES OF
# MERCHANTABILITY OR FITNESS FOR A PARTICULAR PURPOSE. IN NO EVENT
# WILL IBM OR ITS LICENSORS OR SUPPLIERS BE LIABLE FOR ANY DAMAGES
# ARISING OUT OF THE USE OF OR INABILITY TO USE THE SAMPLE CODE OR
# COMBINATION OF THE SAMPLE CODE WITH ANY OTHER CODE. IN NO EVENT
# SHALL IBM OR ITS LICENSORS AND SUPPLIERS BE LIABLE FOR ANY LOST
# REVENUE, LOST PROFITS OR DATA, OR FOR DIRECT, INDIRECT, SPECIAL,
# CONSEQUENTIAL, INCIDENTAL OR PUNITIVE DAMAGES, HOWEVER CAUSED AND
# REGARDLESS OF THE THEORY OF LIABILITY,-, EVEN IF IBM OR ITS
# LICENSORS OR SUPPLIERS HAVE BEEN ADVISED OF THE POSSIBILITY OF SUCH
# DAMAGES.
#
# -----------------------------------------------------------------------------

#######################################################
#
# Sample script to check if all nodes of an Accelerator are in
# installer mode
#
#######################################################

sleeptime=10

if [ -z $MGMTIP ]; then
  echo "usage: This script is used by other scripts and runs on generated configurations."
  echo "       For standalone calls pass the string 'previous' as parameter and set the"
  echo "       following IP addresses as environment variables before calling the script:"
  echo "       MGMTIP             - management IP of the first cluster node"
  echo "       DN1IP, DN2IP, ...  - management IP of the first/second/etc data node"
  exit 0
fi

echo $MGMTIP
echo "rebooting node ${MGMTIP}"
./sample-reboot-to-installer.py ${MGMTIP} ${LPAR_USER} ${LPAR_PASSWORD}

if [ -z $DN1IP ]
then
	echo SN detected: done
        exit 0
	
else
	echo MN detected: rebooting data nodes
        if [ -z $DN1IP ]
        then
        	echo "node ${DN1IP} does not exist, skipping..."
        	exit 0
        else
        	sleep $sleeptime
                echo "rebooting node ${DN1IP}"
                ./sample-reboot-to-installer.py ${DN1IP} ${LPAR_USER} ${LPAR_PASSWORD}
        fi

        if [ -z $DN2IP ]
        then
                echo "node ${DN2IP} does not exist, skipping..."
                exit 0
        else
                sleep $sleeptime
                echo "rebooting node ${DN2IP}"
                ./sample-reboot-to-installer.py ${DN2IP} ${LPAR_USER} ${LPAR_PASSWORD}
        fi

        if [ -z $DN3IP ]
        then
                echo "node ${DN3IP} does not exist, skipping..."
                exit 0
        else
                sleep $sleeptime                
                echo "rebooting node ${DN3IP}"
                ./sample-reboot-to-installer.py ${DN3IP} ${LPAR_USER} ${LPAR_PASSWORD}
        fi

        if [ -z $DN4IP ]
        then
                echo "node ${DN4IP} does not exist, skipping..."
                exit 0
        else
                sleep $sleeptime                
                echo "rebooting node ${DN4IP}"
                ./sample-reboot-to-installer.py ${DN4IP} ${LPAR_USER} ${LPAR_PASSWORD}
        fi

        if [ -z $DN5IP ]
        then
                echo "node ${DN5IP} does not exist, skipping..."
                exit 0
        else
                sleep $sleeptime                
                echo "rebooting node ${DN5IP}"
                ./sample-reboot-to-installer.py ${DN5IP} ${LPAR_USER} ${LPAR_PASSWORD}
        fi

fi

echo reboot to installer: done

