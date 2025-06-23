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
# Sample script to check if a Multi Node Accelerator is available
#
#######################################################

if [ -z $1 ]; then
  echo "usage: This script is used by other scripts and runs on generated configurations."
  echo "       For standalone calls pass the string 'previous' as parameter and set the"
  echo "       following IP addresses as environment variables before calling the script:"
  echo "       MGMTIP             - management IP of the first cluster node"
  echo "       DN1IP, DN2IP, ...  - management IP of the first/second/etc data node"
  exit 0;
elif [ $1 == "previous" ]; then
  echo "using previous definition"
else
  echo "generating definition for $1"
  # invent temp filename
  tmpexport=$(mktemp /tmp/export.XXXXXXX)

  # load environment
  ./generate_json.pl accelerator_configs/ $1 >$tmpexport
  source $tmpexport
fi;

env | grep -E "DN.IP|MGMTIP" | sort

echo $MGMTIP
./sample-check-appliance-node-availability.sh $MGMTIP
RESULTSUM=$?

if [[ 0 -lt $RESULTSUM ]]
then
       echo first node failed
       exit 1
fi

if [ -z $DN1IP ]
then
	echo SN detected: done
	
else
	echo MN detected: checking data nodes
	echo $DN1IP
	./sample-check-appliance-node-availability.sh $DN1IP
        (( RESULTSUM += $? ))

        echo $DN2IP
        ./sample-check-appliance-node-availability.sh $DN2IP
        (( RESULTSUM += $? ))

        echo $DN3IP
        ./sample-check-appliance-node-availability.sh $DN3IP
        (( RESULTSUM += $? ))

        echo $DN4IP
        ./sample-check-appliance-node-availability.sh $DN4IP
        (( RESULTSUM += $? ))

        echo $DN5IP
        ./sample-check-appliance-node-availability.sh $DN5IP
        (( RESULTSUM += $? ))
fi

if [[ 0 -lt $RESULTSUM ]]
then
       echo "${RESULTSUM} data nodes failed to get into appliance mode"
       exit 1
fi

echo "check that cluster is in appliance mode: done"

