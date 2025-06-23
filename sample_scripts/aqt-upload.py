#!/usr/bin/python3
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

###################################################################
#
# Configuration for Db2 Analytics Accelerator for z/OS on IBM Z
# Uploading a new Accelerator image which has been retrieved
# from FixCentral to an existing and configured SSC LPAR.
#
###################################################################


import os
import sys
import json
import logging
import argparse
import time
from lib.aqtSSC import SecureServiceContainerAPI
from lib.aqtSSC import LPARAccess
from lib.aqtSSC import LPARBootDevice

log = None


def has_dasd(dasdId, instances):
    for dasd in instances:
        if dasdId in list(dasd.values()):
            return True
    return False


def panic(self, msg):
    log.critical(msg)
    self.error(msg)


def parseargv(argv):
    """
    Parse the command line options and validates them.
    Return a tuple with the lpar ip, username, password, name of the operation
    and a dict of its parameters.
    """

    parser = argparse.ArgumentParser(
        description="Db2 Analytics Accelerator image upload"
    )

    parser.panic = lambda msg: panic(parser, msg)

    parser.add_argument(
        "lparip",
        metavar="LPAR_IP",
        action="store",
        type=str,
        help="The IP address or FQDN of the SSC LPAR",
    )
    parser.add_argument(
        "lparusername",
        metavar="LPAR_USER",
        action="store",
        type=str,
        help="Name of the Appliance user",
    )
    parser.add_argument(
        "lparpassword",
        metavar="LPAR_PASSWORD",
        action="store",
        type=str,
        help="Password of the Appliance user",
    )
    parser.add_argument(
        "bootdeviceid",
        metavar="BOOTDEVICE_ID",
        action="store",
        type=str,
        help="The device identifier to which the image is to be installed.",
    )
    parser.add_argument(
        "--bootudid",
        dest="boot_udid",
        action="store",
        type=str,
        help="UDID of a SCSI disk in 32 digit hexadecimal format. This parameter is required if device is a SCSI disk.",
    )
    parser.add_argument(
        "--licpath",
        dest="licPath",
        action="store",
        type=str,
        default="lic",
        help="Path where license accept information has been stored (default: lic).",
    )

    parser.add_argument(
        "image",
        metavar="IMAGE_NAME",
        action="store",
        type=str,
        help="Db2 Analytics Accelerator image to install",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        dest="verbose",
        action="count",
        default=0,
        help="Increase output verbosity and logging",
    )

    options = parser.parse_args(argv[1:])

    print("IP address or FQDN of SSC LPAR: ", options.lparip)
    print("Name of Appliance user: ", options.lparusername)
    print("Boot device identifier: ", options.bootdeviceid)

    if options.boot_udid is not None:
        print("  (SCSI only) UDID of SCSI disk: ", options.boot_udid)

        l = len(options.boot_udid)
        if l != 32:
            sys.exit("UDID must be 32 hex digits, got " + str(l))

        # split into old wwpn lun
        options.boot_wwpn = "0x" + options.boot_udid[:16]
        options.boot_lun = "0x" + options.boot_udid[16:]
    else:
        options.boot_wwpn = None
        options.boot_lun = None

    print("License accept path: ", options.licPath)
    print("Image name: ", options.image)

    lparAccess = LPARAccess(options.lparip, options.lparusername, options.lparpassword)
    lparBootDevice = LPARBootDevice(
        options.bootdeviceid, options.boot_wwpn, options.boot_lun
    )
    return (lparAccess, lparBootDevice, options.image, options.licPath, options.verbose)


def main(argv):
    global log
    logging.basicConfig(level=logging.WARNING)
    log = logging.getLogger(os.path.basename(argv[0]))

    print("***********************************************************")
    print()
    print("  Db2 Analytics Accelerator image upload")
    print()
    print("***********************************************************")
    try:
        lparAccess, lparBootDevice, image, licPath, verbose = parseargv(argv)
        # set loglevel, higher levels also set the loglevel of the libraries.
        if verbose >= 1:
            log.setLevel(logging.INFO)
            logging.getLogger("lib.aqtSSC").setLevel(logging.INFO)
        if verbose >= 2:
            log.setLevel(logging.DEBUG)
            logging.getLogger("lib.aqtSSC").setLevel(logging.DEBUG)
        if verbose >= 3:
            logging.getLogger("requests").setLevel(logging.INFO)
            logging.getLogger("urllib3").setLevel(logging.INFO)
        if verbose >= 4:
            logging.getLogger("requests").setLevel(logging.DEBUG)
            logging.getLogger("urllib3").setLevel(logging.DEBUG)

        ssc = SecureServiceContainerAPI(lparAccess)

        appliance_name, appliance_version = ssc.print_and_return_appliance_status(
            lparAccess
        )

        # appliance_name is "Db2 Analytics Accelerator for z/OS"
        # or "Secure Service Container Installer"
        if appliance_name == "Secure Service Container Installer":
            log.debug("Already in installer")
        else:
            if ssc.is_license_accepted():
                print("License has been accepted already")
            else:
                if licPath is not None:
                    if ssc.check_and_apply_license_accept(licPath, appliance_version):
                        print(
                            "License successfully accepted for version %s"
                            % appliance_version
                        )
                else:
                    raise Exception(
                        "License has not been accepted before and no licpath parameter value provided"
                    )

            print("Switch to Installer")
            resultCode = ssc.switch_to_installer()
            log.debug(resultCode)
            if resultCode.status_code != 202:
                print(
                    "*** ERROR: Unable to switch from the Accelerator to the Installer"
                )
                print(
                    "    You have to log into the Appliance first and accept the license agreement"
                )
                print("    or run the license accept script")
                raise Exception("Unable to switch to Installer")

            else:
                log.debug("Switch to installer successfully submitted")
                available = ssc.wait_for_reboot_to_complete(lparAccess, 30)
                ssc = SecureServiceContainerAPI(lparAccess)

        if lparBootDevice.boot_wwpn is None and lparBootDevice.boot_lun is None:
            print(
                "Check if DASD %s is assigned to LPAR" % lparBootDevice.boot_device_id
            )
            resultCode, json, message = ssc.get_ECKD()
            log.debug(resultCode)
            if not has_dasd(lparBootDevice.boot_device_id, json["instances"]):
                raise Exception(
                    "Missing boot DASD {0}".format(lparBootDevice.boot_device_id)
                )

        print("Uploading image: ", image)
        with open(image, "rb") as f:
            resultCode, _, _ = ssc.upload_image(f, lparBootDevice, lparAccess)
            log.debug(resultCode)
            resultCode.raise_for_status()

        # In case uploading the image took longer than session timout, get new token
        ssc = SecureServiceContainerAPI(lparAccess)

        print("Rebooting LPAR")
        resultCode, _, _ = ssc.reboot(lparBootDevice)
        log.debug(resultCode)
        if resultCode.status_code == 202:
            log.debug("LPAR Reboot successfully submitted")
        available = ssc.wait_for_reboot_to_complete(lparAccess, 30)
        print("***********************************************************")
        print("Image upload completed")
        print("***********************************************************")

    except Exception as e:
        log.critical(e)
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main(sys.argv)
