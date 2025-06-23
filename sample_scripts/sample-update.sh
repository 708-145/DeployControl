#!/usr/bin/env bash
# -----------------------------------------------------------------------------
#
# Licensed Materials - Property of IBM
# 5697-DA7
# (C) Copyright IBM Corp. 2018, 2023.
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
# Sample script to update the Accelerator with a 
# new image version
#
#######################################################


#######################################################
# Environment variables used below
# These could be defined in an another script to support
# multiple environments, for example:
# source ./lpar1.sh
#
# LPAR_USER=<SSC user defined in HMC>
# LPAR_PASSWORD=<SSC user password defined in HMC>
# LPAR_IP=<IP address of the LPAR>
# LPAR_BOOTDEV=<Boot device, e.g. 0.0.9c09>
# LPAR_BOOTUDID=<FCP 32 character UDID of the boot LUN>
# LPAR_CFG_FILE=<configuration file>
# LPAR_CRED_FILE=<json credentials definition file for multiple-node deployments>
# 
#
# The image file which is typically retrieved from FixCentral and 
# which will be uploaded to the SSC LPAR with this script
# e.g., /tmp/7.5.0.0-Information_Management-IDAA-Z.image
# Could be provided either by command line parameter
# or by setting the IMAGE environment variable
if [ -z $IMAGE ] && [ $1 ]; then
    IMAGE=$1    
fi     


#
# Check if required environment variables are actually set
#                                              
: "${IMAGE?Please provide image name as commandline parameter or set IMAGE environment variable}"

: "${LPAR_USER?Please set LPAR_USER environment variable}"
: "${LPAR_PASSWORD?Please set LPAR_USER environment variable}"
: "${LPAR_IP?Please set LPAR_IP environment variable}"
: "${LPAR_BOOTDEV?Please set LPAR_BOOTDEV environment variable}"
: "${LPAR_CFG_FILE?Please set LPAR_CFG_FILE environment variable}"



#
# 1. Quiesce appliance
#
./aqt-quiesce.py $LPAR_IP $LPAR_USER $LPAR_PASSWORD --licpath lic
if [ $? -ne 0 ]; then
        echo "Quiesce appliance failed"
	exit 1
fi

                    
#
# 2. Export configuration file to local directory
#
./aqt-export-config.py $LPAR_IP $LPAR_USER $LPAR_PASSWORD $LPAR_CFG_FILE --licpath lic
if [ $? -ne 0 ]; then
        echo "Export configuration file failed"
	exit 1
fi


#
# 3. Upload the Image to the LPAR
#
if [ -z "$LPAR_BOOTUDID" ]; then
    echo "using DASD deployment path"
    ./aqt-upload.py $LPAR_IP $LPAR_USER $LPAR_PASSWORD $LPAR_BOOTDEV $IMAGE --licpath lic
else
    echo "using FCP deployment path"
    ./aqt-upload.py $LPAR_IP $LPAR_USER $LPAR_PASSWORD $LPAR_BOOTDEV --bootudid $LPAR_BOOTUDID $IMAGE --licpath lic
fi
if [ $? -ne 0 ]; then
        echo "Image upload failed"
	exit 1
fi


#
# 4. The updated image could be a new version, In this case, the Licence must be accepted (prompt)
#    Once accepted, information is stored in the specified subdirectory and used for subsequence calls.
#    If license has been accepted before, this script just returns without prompting
#
./aqt-license-accept.py $LPAR_IP $LPAR_USER $LPAR_PASSWORD --licpath lic
if [ $? -ne 0 ]; then
        echo "License accept not successful"
	exit 1
fi


#
# 5. Import configuration and reboot appliance
#
./aqt-import-config.py $LPAR_IP $LPAR_USER $LPAR_PASSWORD $LPAR_CFG_FILE --licpath lic
if [ $? -ne 0 ]; then
        echo "Import configuration file failed"
	exit 1
fi

#
# 6. Multiple node deployments only: complete update with data node credentials
#
if [ -z $LPAR_CRED_FILE ]; then
   echo "Single Node update completed"
  ./sample-wait-operational.py $LPAR_IP $LPAR_USER $LPAR_PASSWORD
else
  ./aqt-complete-update.py $LPAR_IP $LPAR_USER $LPAR_PASSWORD $LPAR_CRED_FILE --licpath lic
fi
