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
# License download, review and accept
# Information about an accepted license version is stored
# locally and considered by subsequent sample script calls.
#
###################################################################


import os
import sys
import json
import logging
import argparse
import time
from lib.aqtSSC import SecureServiceContainerAPI, LPARAccess

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
    parser = argparse.ArgumentParser(
        description="Db2 Analytics Accelerator license management"
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
        "--licpath",
        dest="licPath",
        action="store",
        type=str,
        default="lic",
        help="Path where license information will be stored (default: lic).",
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Do not prompt, but confirm license silently. License files will be downloaded.",
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
    print(f"IP address or FQDN of SSC LPAR: {options.lparip}")
    print(f"Name of Appliance user: {options.lparusername}")
    print(f"License information path: {options.licPath}")
    lparAccess = LPARAccess(options.lparip, options.lparusername, options.lparpassword)
    return (lparAccess, options.licPath, options.confirm, options.verbose)


def main(argv):
    global log
    logging.basicConfig(level=logging.WARNING)
    log = logging.getLogger(os.path.basename(argv[0]))

    print("***********************************************************")
    print()
    print("  Db2 Analytics Accelerator License management")
    print()
    print("***********************************************************")
    try:
        lparAccess, licPath, confirm, verbose = parseargv(argv)
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

        # This is for customer deployments
        # Ask if license is acceptable just as it does in the GUI
        if ssc.license_accept_file_exists(licPath, appliance_version):
            print("***********************************************************")
            print("License has been accepted already")
            print("***********************************************************")
        else:
            lic_filename, non_ibm_lic_filename = ssc.download_license_files(licPath)
            print("***********************************************************")
            print("Please review the Db2 Analytics Accelerator license files")
            print("License file in:          %s" % lic_filename)
            print("Non-IBM license file in:  %s" % non_ibm_lic_filename)
            print("***********************************************************")
            if confirm:
                accept = "y"
            else:
                accept = input("Accept license? (enter 'y'): ")
            if accept == "y" or accept == "yes":
                # write accept file to lic directory
                ssc.write_license_accept_file(licPath, appliance_version)
                # accept license in SSC
                ssc.check_and_apply_license_accept(licPath, appliance_version)
                print("... wait some time for services to become available ...")
                time.sleep(4)
                print("***********************************************************")
                print("License has been accepted successfully")
                print("***********************************************************")
            else:
                raise Exception("License has not been accepted")

    except Exception as e:
        log.critical(e)
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main(sys.argv)
