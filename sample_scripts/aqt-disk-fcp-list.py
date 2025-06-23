#!/usr/bin/python3
# -----------------------------------------------------------------------------
#
# Licensed Materials - Property of IBM
# 5697-DA7
# (C) Copyright IBM Corp. 2019, 2023.
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
# List disk IDs per FCP device
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


log = None


def panic(self, msg):
    log.critical(msg)
    self.error(msg)


def parseargv(argv):
    """
    Parse the command line options and validates them.
    Return a tuple with the lpar ip, username, password, name of the operation
    and a dict of its parameters.
    """

    parser = argparse.ArgumentParser(description="Db2 Analytics Accelerator FCP disks")

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
        metavar="LPAR_USERNAME",
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
        "deviceid",
        metavar="DEVICE_ID",
        action="store",
        type=str,
        help="FCP device bus ID (e.g. 0.0.9100)",
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
    print("FCP device bus ID: ", options.deviceid)
    print("License accept path: %s" % options.licPath)

    lparAccess = LPARAccess(options.lparip, options.lparusername, options.lparpassword)
    return (lparAccess, options.licPath, options.deviceid, options.verbose)


def main(argv):
    global log
    logging.basicConfig(level=logging.WARNING)
    log = logging.getLogger(os.path.basename(argv[0]))

    print("***********************************************************")
    print()
    print("  Db2 Analytics Accelerator list disk IDs per FCP device")
    print()
    print("***********************************************************")
    try:
        lparAccess, licPath, device_id, verbose = parseargv(argv)
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

        ssc.accept_license(lparAccess, licPath, appliance_version)

        print()
        print("Disk IDs")
        print("------------------------------------")
        resultCode, json, _ = ssc.get_fcp_disks(device_id)
        log.debug(resultCode)
        log.debug(json)
        for instance in json["instances"]:
            print((instance["id"]))
        print("------------------------------------")
        print("Total disks: ", len(json["instances"]))

    except Exception as e:
        log.critical(e)
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main(sys.argv)
