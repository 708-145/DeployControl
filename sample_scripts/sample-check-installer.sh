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
# Sample script to check if an Accelerator is in installer mode
#
#######################################################


IP=$1
RETRYTIME=300
RETRYINTERVAL=30

# if no IP then skip OK
if [ -z $IP ]
then
      echo node does not exist, skipping...
      echo "usage: Please provide accelerator management IP as parameter"
      exit 0
else
      echo "checking node ${IP}"
fi

# if curl/wget returns installer signature then OK
# retry for 5mins with sleeptime of 30s
until [[ 0 -lt `wget --no-check-certificate --timeout=5 https://${IP}/ibmapp -qO- | grep installer | wc -l` ]]
do
      if (( RETRYTIME < RETRYINTERVAL ))
      then
            echo "installer on ${IP} did not come up in time. exiting..."
            exit 1
      else
            echo "installer on ${IP} is not up yet. Sleeping for ${RETRYINTERVAL} seconds"
            sleep ${RETRYINTERVAL}
      fi
      (( RETRYTIME -= ${RETRYINTERVAL} ))
      echo "${RETRYTIME} seconds left checking"
done

echo "LPAR ${IP} is in installer mode"
exit 0

