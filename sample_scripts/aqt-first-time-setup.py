#!/usr/bin/python3
# -----------------------------------------------------------------------------
#
# Licensed Materials - Property of IBM
# 5697-DA7
# (C) Copyright IBM Corp. 2018, 2024.
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
# Trigger Accelerator initialization
#
###################################################################


import os
import subprocess
import sys
import json
import logging
import argparse
import time
import re
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
    parser = argparse.ArgumentParser(
        description="Db2 Analytics Accelerator (first-time) initialization"
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
        "def_config_file",
        metavar="DEF_CONFIG_FILE",
        action="store",
        type=str,
        help="Filename of Accelerator definition configuration file",
    )
    parser.add_argument(
        "--credentials_file",
        dest="credentials_file",
        action="store",
        type=str,
        help="Filename of the Data node credentials file (multiple node deployments only)",
    )
    parser.add_argument(
        "--additional_wait_time",
        dest="additional_wait_time",
        action="store",
        type=int,
        help="Additional wait time in minutes for system to become available. Might be needed for many disks.",
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
    print("Accelerator configuration file: ", options.def_config_file)
    if options.credentials_file:
        print("Accelerator credentials file: ", options.credentials_file)
    if options.additional_wait_time:
        print("Additional wait time in minutes: ", options.additional_wait_time)

    print("License accept path: %s" % options.licPath)

    lparAccess = LPARAccess(options.lparip, options.lparusername, options.lparpassword)
    return (
        lparAccess,
        options.def_config_file,
        options.credentials_file,
        options.additional_wait_time,
        options.licPath,
        options.verbose,
        options.lparip,
    )


def main(argv):
    global log
    logging.basicConfig(level=logging.WARNING)
    log = logging.getLogger(os.path.basename(argv[0]))

    print("***********************************************************")
    print()
    print("  Db2 Analytics Accelerator (first-time) initialization")
    print()
    print("***********************************************************")
    try:
        (
            lparAccess,
            def_config_file,
            credentials_file,
            additional_wait_time,
            licPath,
            verbose,
            lparip,
        ) = parseargv(argv)
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

        print("wait for license accept to come up...")
        time.sleep(180)
        ssc.accept_license(lparAccess, licPath, appliance_version)

        print()
        _, json, _ = ssc.validate_configuration(def_config_file)
        log.debug(json)
        status = json["validation"]
        try:
            message = json["message"][0]

        except Exception as e:
            print(str(e) + ": Continue with empty message")
            message = ""

        log.debug(status)
        log.debug(message)
        if status != "OK":
            raise Exception(
                "Configuration validation failed with status "
                + status
                + '. Message "'
                + message
                + '"'
            )
        print()
        print("Configuration validation successful")

        # If a config file upload happens quickly after system (re) start,
        # it might fail because the back-end service is still initializing
        # In this case, the service request returns an error and has to be re-tried after some time.
        status = ""
        first_time_setup_retry_attempts = 5
        for t in range(first_time_setup_retry_attempts):
            try:
                resultCode, json, _ = ssc.accelerator_first_time_setup(
                    def_config_file, credentials_file
                )
                log.debug(resultCode.status_code)
                if resultCode.status_code == 200:
                    log.debug(json)
                    status = json["status"]
                    log.debug(status)
                    if status != "TRIGGERED":
                        # http call was successful, but service failed
                        raise Exception("First time setup call failed " + status)
                    break
                log.debug("First time setup returned unexpected status, try again")
            except:
                log.debug("First time setup returned an exception, try again")
            # In case of HHTP error or unexpected status code, retry
            time.sleep(15)

        if status != "TRIGGERED":
            raise Exception("First time setup failed")

        print()
        print("First time setup triggered (please wait)")

        attempts = 160
        if additional_wait_time:
            # additional_wait_time are minutes,
            # each loop takes 40 seconds
            attempts += int(additional_wait_time * 60 / 40)
        print("additional_wait_time: ", additional_wait_time)

        status = ssc.wait_until_accelerator_is_starting(lparAccess, attempts, 15)
        log.debug(status)

    except Exception as e:
        log.critical(e)
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main(sys.argv)
