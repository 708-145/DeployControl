#!/usr/bin/env python3
# -----------------------------------------------------------------------------
#
# Licensed Materials - Property of IBM
# 5697-DA7
# (C) Copyright IBM Corp. 2018, 2025.
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
# Utility functions to handle SSC and
# Db2 Analytics Accelerator for z/OS on IBM Z REST API calls.
#
###################################################################


import json
import logging
import os
import subprocess
import io
import time
import datetime
import shutil
import requests
import random
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
requests.packages.urllib3.disable_warnings()

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


class LPARAccess(object):
    """
    An object describing the target SSC LPAR
    by address, username and password
    """

    def __init__(self, address, username, password):
        self.address = address
        self.username = username
        self.password = password

    def set(self, address=None, username=None, password=None):
        self.address = address
        self.username = username
        self.password = password


class LPARBootDevice(object):
    """
    An object describing the target SSC LPAR boot device
    wwpn and lun are only used for SCSI devices
    """

    def __init__(self, boot_device_id, boot_wwpn, boot_lun):
        self.boot_device_id = boot_device_id
        self.boot_wwpn = boot_wwpn
        self.boot_lun = boot_lun

    def set(self, boot_device_id=None, boot_wwpn=None, boot_lun=None):
        self.boot_device_id = boot_device_id
        self.boot_wwpn = boot_wwpn
        self.boot_lun = boot_lun

    def get_udid(self):
        if self.boot_wwpn is not None and self.boot_lun is not None:
            _wwpn = self.boot_wwpn
            _lun = self.boot_lun

            # Check for leading 0x in lun and wwpn
            if _wwpn.startswith("0x") or _wwpn.startswith("0X"):
                _wwpn = _wwpn[2:]
            if _lun.startswith("0x") or _lun.startswith("0X"):
                _lun = _lun[2:]
            return _wwpn + _lun

        return None


class SecureServiceContainerAPI(object):
    """
    Perform API requests against the SSC LPAR
    """

    _lpar_address = None
    _header = dict()

    def __init__(self, lpar_access):
        """
        Initialize object and set default headers
        Request and set the authentication token needed to interface with the API

        Parameters:
          lpar_access (Object): Adress of the LPAR, username and password
          lpar (string): Address of the LPAR, either IP or FQDN
        """
        self.getApiToken(lpar_access)

    def _try_decode_content(self, response):
        """
        Decode the data contained in the response to json, if possible

        Parameters:
          response (requests.Response): The response of the API request

        Returns:
          tuple(json, message), where:
          * json (dict): None if message is not valid json, else the converted (string to dict) message
          * message (string): Data returned by the request

        Raises:
          Does not raise any Exception
        """
        try:  # return json if possible
            return (response.json(), response.content)
        except:
            return (None, response.content)

    def _get_data(self, response):
        """
        Check if response is valid and return its data, else log error and raise an exception

        Parameters:
          response (requests.Response): The response of the API request

        Returns:
          tuple(json, message), where:
          * json (dict): None if message is not valid json, else the converted (string to dict) message
          * message (string): Data returned by the request

        Raises:
          requests.HTTPError if the request did not succeed
        """
        try:
            response.raise_for_status()
        except Exception as e:
            (jsn, msg) = self._try_decode_content(response)
            msg = json.dumps(jsn, indent=4, sort_keys=True) if jsn else msg
            log.error(msg)
            raise e
        return self._try_decode_content(response)

    def _get(self, url, header, stream=False):
        """
        Perform GET request against the API

        Parameters:
          url (string): The FQDN of the URL to query
          header (dict): HTTP Headers to send
          stream (bool): Enable streaming (default: False)

        Returns:
          requests.Response of the API call
        """
        url = "https://{0}{1}".format(self._lpar_address, url)
        log.debug("GET: %s" % url)
        return requests.get(url, headers=header, verify=False, stream=stream)

    def _post(self, url, header, data=None):
        """
        Perform POST request against the API

        Parameters:
          url (string): The FQDN of the URL to query
          header (dict): HTTP Headers to send
          data (binary): The data to send

        Returns:
          requests.Response of the API call
        """
        url = "https://{0}{1}".format(self._lpar_address, url)
        log.debug("POST: %s" % url)
        return requests.post(url, headers=header, verify=False, data=data)

    def _put(self, url, header, data=None):
        """
        Perform PUT request against the API

        Parameters:
          url (string): The FQDN of the URL to query
          header (dict): HTTP Headers to send
          data (binary): The data to send

        Returns:
          requests.Response of the API call
        """
        url = "https://{0}{1}".format(self._lpar_address, url)
        log.debug("PUT: %s" % url)
        return requests.put(url, headers=header, verify=False, data=data)

    def get(self, url):
        """
        Perform GET request with the default headers against the API

        Parameters:
          url (string): The FQDN of the URL to query

        Returns:
          requests.Response of the API call
        """
        response = self._get(url, self._header)
        return (response,) + self._get_data(response)

    def post(self, url, data=None):
        """
        Perform POST request with the default headers against the API

        Parameters:
          url (string): The FQDN of the URL to query
          data (binary): The data to send

        Returns:
          requests.Response of the API call
        """
        response = self._post(url, self._header, data)
        return (response,) + self._get_data(response)

    def put(self, url, data=None):
        """
        Perform PUT request with the default headers against the API

        Parameters:
          url (string): The FQDN of the URL to query
          data (binary): The data to send

        Returns:
          requests.Response of the API call
        """
        response = self._put(url, self._header, data)
        return (response,) + self._get_data(response)

    ###################################################################

    def getApiToken(self, lpar_access):
        """
        Request and set the authentication token needed to interface with the API

        Parameters:
          lpar_access (Object): Adress of the LPAR, username and password
          lpar (string): Address of the LPAR, either IP or FQDN
        """
        self._header = {
            "Accept": "application/vnd.ibm.zaci.payload+json",
            "zACI-API": "com.ibm.zaci.system/1.0",
            "Content-Type": "application/vnd.ibm.zaci.payload+json;version=1.0",
        }
        self._lpar_address = lpar_access.address

        url = "/api/com.ibm.zaci.system/api-tokens"
        data = json.dumps(
            {
                "kind": "request",
                "parameters": {
                    "user": lpar_access.username,
                    "password": lpar_access.password,
                },
            }
        )
        (response, jsn, content) = self.post(url, data)
        token = jsn["parameters"]["token"]
        self._header["Authorization"] = "Bearer " + token

    def get_fcp_disks(self, device_bus_id):
        url = (
            "/api/com.ibm.zaci.system/fcp-disks?fcp-device={device}&status=free".format(
                device=device_bus_id
            )
        )
        return self.get(url)

    def get_ECKD(self):
        url = "/api/com.ibm.zaci.system/storage-devices?type=ECKD"
        return self.get(url)

    def upload_image(self, image, lpar_boot_device, lpar_access):
        url = "/api/com.ibm.zaci.system/sw-appliances/install?id={device_id}"

        _wwpn = None
        _lun = None
        _dev = None
        _device = lpar_boot_device.boot_device_id
        _udid = lpar_boot_device.get_udid()

        if _udid:
            max_attempts = 10
            success = False
            triggerurl = "/api/com.ibm.zaci.system/fcp-disks?fcp-device=" + _device
            url = url + "&wwpn={wwpn}&lun={lun}"

            for attempt_number in range(max_attempts):
                try:
                    print("FCP discovery attempt #" + str(attempt_number))

                    # refresh API token
                    self.getApiToken(lpar_access)

                    # trigger FCP discovery
                    _discovery = self.get(triggerurl)

                    # sleep while async discovery runs
                    time.sleep(120)

                    # get FCP path
                    _path = self.get_fcp_path_by_udid([_device], _udid)
                    if _path:
                        _wwpn, _lun, _dev = _path  # target wwpn and lun
                        success = True
                        break
                except Exception as e:
                    print("FCP discovery exception 1: " + str(e))

            if not success:
                raise Exception(
                    "Cannot upload image to "
                    + self._lpar_address
                    + " with "
                    + "udid "
                    + _udid
                    + ", "
                    + "device "
                    + _device
                    + "."
                )
            else:
                print("FCP discovery successful")

        header = self._header.copy()
        header["Content-type"] = "application/octet-stream"
        if isinstance(image, io.IOBase):
            log.debug(os.fstat(image.fileno()))
            header["Content-length"] = "{0}".format(os.fstat(image.fileno()).st_size)
        else:
            header["Content-length"] = "{0}".format(len(image))

        response = self._post(
            url.format(device_id=_device, wwpn=_wwpn, lun=_lun), header, image
        )
        return (response, None, "")

    def switch_to_installer(self):
        url = "/api/com.ibm.zaci.system/maintenance-actions/switch-to-installer"
        return self._post(url, self._header)

    def get_maintenance_actions(self):
        url = "/api/com.ibm.zaci.system/maintenance-actions"
        return self.get(url)

    def reboot(self, lpar_boot_device):
        url = "/api/com.ibm.zaci.system/sw-appliances/select"

        _device = lpar_boot_device.boot_device_id
        _udid = lpar_boot_device.get_udid()

        if _udid:
            # FCP
            _path = self.get_fcp_path_by_udid([_device], _udid)
            if _path:
                _wwpn, _lun, _dev = _path  # target wwpn and lun
            else:
                raise Exception(
                    "Cannot activate "
                    + self._lpar_address
                    + " using "
                    + "udid "
                    + _udid
                    + " with  "
                    + "device "
                    + _dev
                    + "."
                )

            data = json.dumps(
                {
                    "kind": "request",
                    "parameters": {
                        "disk": {"id": _dev, "wwpn": _wwpn, "lun": _lun},  # FCP
                        "reboot-after": True,
                    },
                }
            )
        else:
            data = json.dumps(
                {
                    "kind": "request",
                    "parameters": {
                        "disk": {"id": _device},  # DASD
                        "reboot-after": True,
                    },
                }
            )
        return self.put(url, data)

    def get_appliance_status(self):
        url = "/api/com.ibm.zaci.system/appliance"
        return self.get(url)

    def get_appliance_operational(self):
        url = "/api/com.ibm.zaci.system/appliance/is-operational"
        return self.get(url)

    def ping_appliance(self, timeout):
        url = "https://{0}{1}".format(self._lpar_address, "/")
        log.debug("GET: %s" % url)
        log.debug("With timeout: %d" % timeout)
        try:
            r = requests.get(url, verify=False, timeout=timeout)
            log.debug(r)
        except Exception as e:
            log.debug(e)
            return False
        return True

    def is_license_accepted(self):
        url = "/api/com.ibm.zaci.system/software-license"
        resultCode, json, message = self.get(url)
        log.debug(resultCode)
        log.debug(json)
        return json["properties"]["accepted"]

    def accelerator_first_time_setup(self, config_file, credentials_file):
        url = "/api/com.ibm.aqt/configuration"
        config_data = None
        credentials = None
        with open(config_file, "r") as file:
            config_data = json.load(file)
        if credentials_file:
            with open(credentials_file, "r") as file:
                credentials = json.load(file)
        data = json.dumps(
            {
                "kind": "request",
                "parameters": {
                    "configuration": config_data,
                    "credentials": credentials,
                },
            }
        )
        return self.put(url, data)

    def validate_configuration(self, config_file):
        url = "/api/com.ibm.aqt/configuration/validate_config"
        config_data = None
        with open(config_file, "r") as file:
            config_data = json.load(file)
        data = json.dumps({"kind": "request", "parameters": config_data})
        return self.put(url, data)

    def get_accelerator_status(self):
        url = "/api/com.ibm.aqt/components/appliance"
        resultCode, json, message = self.get(url)
        log.debug(resultCode)
        return json["status"]

    def get_accelerator_server_status(self):
        url = "/api/com.ibm.aqt/components/accelerator_server"
        resultCode, json, message = self.get(url)
        log.debug(resultCode)
        return json["status"]

    def export_configuration(self):
        print("exporting using 3 REST calls...")
        url = "/api/com.ibm.aqt/cluster/export_ssc_config"
        header = self._header.copy()
        header["Accept"] = "application/octet-stream"
        data = json.dumps(
            {
                "kind": "request",
                "parameters": {"description": "Db2 Analytics Accelerator"},
            }
        )
        self.put(url, data)
        url = "/api/com.ibm.zaci.system/appliance-configuration/export"
        response = self._post(url, header, data)
        url = "/api/com.ibm.aqt/components/exportcleanup"
        self.put(url)
        return (response,) + self._get_data(response)

    def import_configuration(self, configuration_file):
        url = "/api/com.ibm.zaci.system/appliance-configuration/import?apply_now=true"
        header = self._header.copy()
        header["Content-type"] = "application/octet-stream"
        if isinstance(configuration_file, io.IOBase):
            log.debug(os.fstat(configuration_file.fileno()))
            header["Content-length"] = "{0}".format(
                os.fstat(configuration_file.fileno()).st_size
            )
        else:
            header["Content-length"] = "{0}".format(len(configuration_file))
        response = self._post(url, header, configuration_file)
        return response

    def take_concurrent_dump(self, dumpname, retry_delay=15, max_retries=10):
        # trigger concurrent dump
        url = "/api/com.ibm.zaci.system/alerts"
        payload = json.dumps({"kind": "request", "parameters": {"reason": dumpname}})
        _, jsonPost, _ = self.post(url, payload)
        self_url = jsonPost["parameters"]["self"]
        # wait for completion
        current_retries = 0
        while current_retries < max_retries:
            response, jsonGet, message = self.get(self_url)
            if jsonGet and jsonGet["kind"] == "response":
                print("progress:", jsonGet["parameters"]["percent-complete"], "%")

            if jsonGet and jsonGet["kind"] == "instance":
                print("Dump ready for download")
                return response.status_code

            current_retries += 1
            time.sleep(retry_delay)

        print("taking the dump took too long. Giving up.")
        return response.status_code

    def save_dump(self, dump_filename):
        # find latest dump. All dumps have msgid 'AZIZ0001E'
        url = "/api/com.ibm.zaci.system/alerts"
        _, jsonDump, _ = self.get(url)
        matching_entries = [
            entry for entry in jsonDump["instances"] if entry["msgid"] == "AZIZ0001E"
        ]
        latest_self_url = max(matching_entries, key=lambda x: x["timestamp"])["self"]
        dump_url = latest_self_url + "/diag-info"
        print(dump_url)
        # download dump
        header = self._header.copy()
        header["Accept"] = "application/octet-stream"
        response = self._get(dump_url, header)
        # save dump to file
        with open(dump_filename, "wb") as file:
            file.write(response.content)
        return response.status_code

    def quiesce_force(self):
        url = "/api/com.ibm.aqt/components/quiesce/force"
        return self.put(url)

    def complete_update(self, credentials_file):
        url = "/api/com.ibm.aqt/cluster/update_data_nodes_with_credentials"
        credentials = None
        with open(credentials_file, "r") as file:
            credentials = json.load(file)
        data = json.dumps(
            {"kind": "request", "parameters": {"credentials": credentials}}
        )
        return self.put(url, data)

    def reset(self):
        url = "/api/com.ibm.aqt/components/reset"
        return self.put(url)

    def reset_wipe(self):
        url = "/api/com.ibm.aqt/components/reset/wipe"
        return self.put(url)

    ###################################################################

    def download_license_files(self, lic_path):
        if not os.path.exists(lic_path):
            os.makedirs(lic_path)
        resultCode, json, message = self.get("/License/Lic_en-US.txt")
        log.debug(resultCode)
        lic_filename = os.path.join(lic_path, "Lic_en-US.txt")
        with open(lic_filename, "w") as lic_file:
            lic_file.write(str(message))
        resultCode, json, message = self.get("/Non_IBM_License/non_ibm_license.txt")
        log.debug(resultCode)
        non_ibm_lic_filename = os.path.join(lic_path, "non_ibm_license.txt")
        with open(non_ibm_lic_filename, "w") as non_ibm_lic_file:
            non_ibm_lic_file.write(str(message))
        return (lic_filename, non_ibm_lic_filename)

    def write_license_accept_file(self, lic_path, ver):
        if not os.path.exists(lic_path):
            os.makedirs(lic_path)
        lic_acc_filename = os.path.join(lic_path, ver + ".accept")
        log.debug(lic_acc_filename)
        with open(lic_acc_filename, "w") as file:
            file.write(str(datetime.datetime.now()))
        return lic_acc_filename

    def license_accept_file_exists(self, lic_path, ver):
        log.debug("lic_path: %s" % lic_path)
        log.debug("version: %s" % ver)
        if os.path.exists(lic_path):
            if os.path.exists(lic_path + "/" + ver + ".accept"):
                log.debug("License for this version has been accepted previously")
                return True
        return False

    def check_and_apply_license_accept(self, lic_path, ver):
        """
        Check if there is a file which denotes previous licence
        acceptance for this version.
        If so, accept license for installed product
        """
        log.debug("lic_path: %s" % lic_path)
        log.debug("version: %s" % ver)
        if os.path.exists(lic_path):
            if os.path.exists(lic_path + "/" + ver + ".accept"):
                log.debug("License for this version has been accepted previously")
                url = "/api/com.ibm.zaci.system/software-license"
                data = json.dumps({"kind": "request", "parameters": {"accept": True}})
                response = requests.put(
                    "https://{0}{1}".format(self._lpar_address, url),
                    headers=self._header,
                    verify=False,
                    data=data,
                )
                log.debug(response)
                if response.status_code == 200:
                    log.debug("License accepted successfully")
                    available = False
                    attempts = 20
                    while not available and attempts > 0:
                        time.sleep(5)
                        available = True
                        attempts -= 1
                        log.debug("Check appliance operational")
                        (
                            resultCode,
                            jsonthing,
                            message,
                        ) = self.get_appliance_operational()
                        log.debug(resultCode)
                        log.debug(jsonthing)
                        if resultCode.status_code != 204:
                            log.debug("The appliance is not yet operational.")
                            available = False
                else:
                    raise Exception("License accept failed")

            else:
                raise Exception(
                    "License for this version has not been accepted previously"
                )
        else:
            raise Exception("License accept path does not exist")
        return True

    def get_fcp_data(self, device):
        """
        GET https://<ip-address>1/api/com.ibm.zaci.system/fcp-disks?fcp-device=<device>
        returns response[1] including all instances (=udids) with all paths (target_wwpn+lun)
        """
        attempt_count = 0
        while attempt_count < 6:
            if attempt_count > 0:
                time.sleep(15)
            attempt_count += 1
            try:
                response = self.get_fcp_disks(device)
                if response and (response[0].status_code == 200):
                    data = response[1]

                    instance_count = 0
                    if data.get("instances"):
                        instance_count = len(data["instances"])
                    if instance_count == 0:
                        raise Exception("Received no instances.")

                    log.debug(
                        "get_fcp_data: returning data, number of instances is "
                        + str(instance_count)
                        + "."
                    )
                    return data

                else:
                    raise Exception("GET response " + str(response[0].status_code))
            except Exception as e:
                log.debug("get_fcp_data: Exception " + str(e))
        raise Exception("get_fcp_data: No FCP data for device " + device)

    def get_fcp_path_by_udid(self, devices, udid):
        """
        returns random path as (wwpn, lun, device) if at least one path exists,
        None otherwise
        """

        log.debug(f"get_fcp_path_by_udid: entering with {devices}")

        attempt_count = 0
        while attempt_count < 6:
            all_paths = list()  # all active paths to udid
            for device in devices:
                if len(device) == 4:
                    device = (
                        "0.0." + device
                    )  # fixing device here, too, because it's returned
                data = self.get_fcp_data(device)
                all_matching_instances = list()  # all instances with matching udid
                # should be exactly one
                if data:
                    for instance in data["instances"]:
                        if instance.get("status") and (instance["status"] == "free"):
                            local_udid = instance["id"]
                            if len(local_udid) == 33:
                                local_udid = local_udid[1:]
                            if udid == local_udid:
                                all_matching_instances.append(instance)

                golden_instance = None  # first instance with matching udid
                if len(all_matching_instances) >= 1:
                    golden_instance = all_matching_instances[0]

                    if golden_instance.get("paths"):
                        for path in golden_instance["paths"]:
                            if path.get("status") and (path["status"] == "active"):
                                all_paths.append(path)

            if len(all_paths) >= 1:
                # pick random path
                path = all_paths[random.randint(0, len(all_paths) - 1)]
                retval = (path["target"], path["lun"], device)
                log.debug(
                    "get_fcp_path_by_udid: returning "
                    + str(retval)
                    + " for udid "
                    + udid
                )
                return retval

            attempt_count += 1
            time.sleep(15)

        log.debug(
            "get_fcp_path_by_udid: No FCP path found on "
            + self._lpar_address
            + " for "
            + "udid "
            + udid
            + " using "
            + "device "
            + device
        )
        return None

    ###################################################################

    def print_and_return_appliance_status(
        self,
        lparAccess,
    ):
        """
        gets and prints appliance status
        """

        self.getApiToken(lparAccess)
        resultCode, json, message = self.get_appliance_status()
        log.debug("Appliance status:")
        log.debug(resultCode)
        log.debug(json)
        appliance_properties = json["properties"]
        appliance_name = appliance_properties["name"]
        appliance_version = appliance_properties["version"]
        print("***********************************************************")
        print("Appliance name: ", appliance_name)
        print("Version: ", appliance_version)
        print("Physical Server Name: ", appliance_properties["physical-server-name"])
        print("Virtual Server Name: ", appliance_properties["virtual-server-name"])
        print("***********************************************************")

        # appliance_name is "Db2 Analytics Accelerator for z/OS"
        # or "Secure Service Container Installer"
        if appliance_name != "Db2 Analytics Accelerator for z/OS":
            print("LPAR not Db2 Analytics Accelerator (%s): " % appliance_name)
            log.debug("Not in Accelerator Appliance but: ", appliance_name)

        return appliance_name, appliance_version

    def accept_license(self, lparAccess, licPath, appliance_version):
        """
        accepts the license if not already accepted
        """

        self.getApiToken(lparAccess)
        if self.is_license_accepted():
            print("License has been accepted already")
        else:
            if licPath is not None:
                if self.check_and_apply_license_accept(licPath, appliance_version):
                    print(
                        "License successfully accepted for version %s"
                        % appliance_version
                    )
            else:
                raise Exception(
                    "License has not been accepted before and no licpath parameter value provided"
                )

    def wait_until_accelerator_is_operational(
        self, lparAccess, attempts, token_refresh_time
    ):
        """
        waits for 'attempts' 40s steps that the accelerator becomes operational
        refreshes access token every 'token_refresh_time' steps
        """

        print("Wait for operational accelerator")

        # get a new token before waiting
        self.getApiToken(lparAccess)

        attempts = attempts
        status = self.get_accelerator_status()
        log.debug(status)
        while status != "READY" and attempts > 0:
            attempts -= 1
            log.debug("attempts %d" % attempts)
            time.sleep(40)

            if attempts % token_refresh_time == 0:
                self.getApiToken(lparAccess)

            status = self.get_accelerator_status()
            print("... ", status)

        if attempts == 0:
            raise Exception("Accelerator base did not come up in time")

        print
        print("***********************************************************")
        print("Accelerator base started successfully")
        print("***********************************************************")

    def wait_until_accelerator_is_starting(
        self, lparAccess, attempts, token_refresh_time
    ):
        """
        waits for 'attempts' 40s steps that the accelerator ist starting
        refreshes access token every 'token_refresh_time' steps
        """

        print("Wait for starting accelerator")

        # get a new token before waiting
        self.getApiToken(lparAccess)

        attempts = attempts
        status = self.get_accelerator_status()
        log.debug(status)
        while status != "STARTING" and attempts > 0:
            attempts -= 1
            log.debug("attempts %d" % attempts)
            time.sleep(40)

            if attempts % token_refresh_time == 0:
                self.getApiToken(lparAccess)

            status = self.get_accelerator_status()
            print("... ", status)

        if attempts == 0:
            raise Exception("Accelerator base did not come up in time")

        print
        print("***********************************************************")
        print("Accelerator is starting")
        print("***********************************************************")

    def wait_until_update_credentials(self, lparAccess, attempts, token_refresh_time):
        """
        waits for 'attempts' 40s steps that the accelerator reaches credentials input state
        refreshes access token every 'token_refresh_time' steps
        """

        print("Wait for credential update")

        # get a new token before waiting
        self.getApiToken(lparAccess)

        attempts = attempts
        status = status = self.get_accelerator_status()
        log.debug(status)
        while status != "UPDATE_CLUSTER_WAIT_CREDENTIALS" and attempts > 0:
            attempts -= 1
            log.debug("attempts %d" % attempts)
            time.sleep(40)
            if attempts % token_refresh_time == 0:
                self.getApiToken(lparAccess)
            status = self.get_accelerator_status()
            print("... (waiting for UPDATE_CLUSTER_WAIT_CREDENTIALS)", status)

        if attempts == 0:
            raise Exception(
                "Waiting for UPDATE_CLUSTER_WAIT_CREDENTIALS did not complete in time"
            )

    def wait_until_server_is_operational(
        self, lparAccess, attempts, token_refresh_time
    ):
        """
        waits for 'attempts' 40s steps that the server becomes operational
        refreshes access token every 'token_refresh_time' steps
        """

        print("Wait for server start")

        # get a new token before waiting
        self.getApiToken(lparAccess)

        acceleratorServerStatus = self.get_accelerator_server_status()
        log.debug(acceleratorServerStatus)
        attempts = attempts
        while acceleratorServerStatus != "RUNNING" and attempts > 0:
            attempts -= 1
            log.debug("attempts %d" % attempts)
            time.sleep(40)

            acceleratorServerStatus = self.get_accelerator_server_status()
            if acceleratorServerStatus == "RUNNING":
                print("... RUNNING")
            else:
                log.debug(acceleratorServerStatus)
                print("... STARTING")

            if attempts % token_refresh_time == 0:
                self.getApiToken(lparAccess)

            with open(os.devnull, "w") as DEVNULL:
                try:
                    subprocess.check_call(
                        ["ping", "-c", "1", lparAccess.address],
                        stdout=DEVNULL,  # suppress output
                        stderr=DEVNULL,
                    )
                    print(lparAccess.address, "is pingable")
                except subprocess.CalledProcessError:
                    print(lparAccess.address, "is NOT pingable")

        if attempts == 0:
            raise Exception("Accelerator components did not come up in time")

        print
        print("***********************************************************")
        print("Accelerator started successfully and is ready to use")
        print("***********************************************************")

    def wait_for_reboot_to_complete(self, lparAccess, attempts):
        """
        After a reboot request, poll the server until it responds again.
        Or return False after some defined retry attempts.
        """

        log.debug("Wait until reboot completed")
        attempts = attempts
        available = False
        print("The appliance is rebooting. Please wait.")
        while not available and attempts > 0:
            attempts -= 1
            print("... ", attempts)
            log.debug("attempts %d" % attempts)
            time.sleep(30)
            log.debug("Ping appliance with 5 seconds timeout")
            available = self.ping_appliance(5)
            log.debug(available)

        if available == True:
            # after reboot, the API token needs to be re-established (new log in)
            self.getApiToken(lparAccess)
            log.debug("Get appliance status")
            resultCode, json, message = self.get_appliance_status()
            log.debug(resultCode)
            log.debug(json)
            if resultCode.status_code == 503:
                log.debug("The appliance is rebooting.")
                available = False
            elif resultCode.status_code == 200:
                appliance_name = json["properties"]["name"]
                print("Appliance name: ", appliance_name)
                log.debug("Appliance name: " + appliance_name)
            else:
                log.debug(resultCode.status_code)
        else:
            raise Exception("Reboot did not complete in time")

        return available

    ###################################################################
