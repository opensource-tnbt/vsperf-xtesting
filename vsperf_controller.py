# Copyright 2018-19 Spirent Communications.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
VSPERF-controller
"""

# Fetching Environment Variable for controller, You can configure or
# modifies list.env file for setting your environment variable.

#pylint: disable=global-statement,no-else-continue
#pylint: disable=too-many-branches

import os
import time
import math
import ast
import ssh
import sys
import paramiko
import tarfile

_ONE_DAY_IN_SECONDS = 60 * 60 * 24
TIMER = float()


DUT_IP = os.getenv('DUT_IP_ADDRESS')
DUT_USER = os.getenv('DUT_USERNAME')
DUT_PWD = os.getenv('DUT_PASSWORD')
VSPERF_TEST = os.getenv('VSPERF_TESTS')
VSPERF_CONF = os.getenv('VSPERF_CONFFILE')
VSPERF_TRAFFICGEN_MODE = str(os.getenv('VSPERF_TRAFFICGEN_MODE'))
DUT_CLIENT = None
TGEN_CLIENT = None
SANITY_CHECK_DONE_LIST = list()


def host_connect():
    """
    Handle host connectivity to DUT
    """
    global DUT_CLIENT
    DUT_CLIENT = ssh.SSH(host=DUT_IP, user=DUT_USER, password=DUT_PWD)
    print("DUT Successfully Connected ..............................................[OK] \n ")

def upload_test_config_file():
    """
    #Upload Test Config File on DUT
    """
    #localpath = '/usr/src/app/vsperf/vsperf.conf'
    localpath = 'vsperf.conf'
    if not os.path.exists(localpath):
        print("VSPERF Test config File does not exists.......................[Failed]")
        return
    remotepath = '~/vsperf.conf'
    check_test_config_cmd = "find ~/ -maxdepth 1 -name '{}'".format(
        remotepath[2:])
    check_test_result = str(DUT_CLIENT.execute(check_test_config_cmd)[1])
    if remotepath[2:] in check_test_result:
        DUT_CLIENT.run("rm -f {}".format(remotepath[2:]))
    DUT_CLIENT.put_file(localpath, remotepath)
    check_test_config_cmd_1= "find ~/ -maxdepth 1 -name '{}'".format(
        remotepath[2:])
    check_test_result_1= str(DUT_CLIENT.execute(check_test_config_cmd)[1])
    if remotepath[2:] in check_test_result_1:
    	print(
        "Test Configuration File Uploaded on DUT-Host.............................[OK] \n ")
    else:
    	print("VSPERF Test config file upload failed.....................................[Critical]")

def run_vsperf_test():
    """
    Here we will perform the actual vsperf test
    """
    global TIMER
    rmv_cmd = "cd /mnt/huge && echo {} | sudo -S rm -rf *".format(DUT_PWD)
    DUT_CLIENT.run(rmv_cmd, pty=True)
    cmd = "source ~/vsperfenv/bin/activate ; "
    #cmd = "scl enable python33 bash ; "
    cmd += "cd vswitchperf && "
    cmd += "./vsperf "
    if VSPERF_CONF:
        cmd += "--conf-file ~/vsperf.conf "
    if "yes" in VSPERF_TRAFFICGEN_MODE.lower():
        cmd += "--mode trafficgen"
    vsperf_test_list = VSPERF_TEST.split(",")
    print(vsperf_test_list)
    for test in vsperf_test_list:
        atest = cmd
        atest += test
        DUT_CLIENT.run(atest, pty=True)
    print(
        "Test Successfully Completed................................................[OK]\n ")


def test_status():
    """
    Chechk for the test status after performing test
    """
    testtype_list = VSPERF_TEST.split(",")
    num_test = len(testtype_list)
    test_success = []
    test_failed = []
    testtype_list_len = len(testtype_list)
    for test in testtype_list:
        passed_minutes = 5
        latest_result_cmd = "find /tmp -mindepth 1 -type d -cmin -{} -printf '%f'".format(
            passed_minutes)
        test_result_dir = str(
            (DUT_CLIENT.execute(latest_result_cmd)[1]).split('find')[0])
        test_date_cmd = "date +%F"
        test_date = str(DUT_CLIENT.execute(test_date_cmd)[1]).replace("\n", "")
        if test_date in test_result_dir:
            testcase_check_cmd = "cd /tmp && cd `ls -t | grep results | head"
            testcase_check_cmd += " -{} | tail -1` && find . -maxdepth 1 -name '*{}*'".\
                                  format(testtype_list_len, test)
            testcase_check_output = str(
                DUT_CLIENT.execute(testcase_check_cmd)[1]).split('\n', 2)
            check = 0
            for i in testcase_check_output:
                if (".csv" in i) or (".md" in i) or (".rst" in i):
                    check += 1
            if check == 3:
                test_success.append(test)
            else:
                test_failed.append(test)
            testtype_list_len -= 1
    if num_test == len(test_success):
        print("All Test Successfully Completed on DUT-Host   Results... [OK]")
    elif not test_success:
        print("All Test Failed on DUT-Host \nResults... [Failed]")
    else:
        print(
            "Only {} Test failed    Results ... [Failed]\n"\
            "All other Test Successfully Completed on DUT-Host     Results... [OK] ".\
            format(test_failed))


def sanity_vsperf_check():
    """
    We have to make sure that VSPERF is installed correctly
    """
    global SANITY_CHECK_DONE_LIST
    vsperf_check_command = "source ~/vsperfenv/bin/activate ; cd vswitchperf* && ./vsperf --help"
    vsperf_check_cmd_result = str(DUT_CLIENT.execute(vsperf_check_command)[1])
    vsperf_verify_list = [
        'usage',
        'positional arguments',
        'optional arguments',
        'test selection options',
        'test behavior options']
    for idx, i in enumerate(vsperf_verify_list, start=1):
        if str(i) in vsperf_check_cmd_result:
            if idx < 5:
                continue
            elif idx == 5:
                SANITY_CHECK_DONE_LIST.append(int(3))
                print("VSPERF Installed Correctly and Working fine......................." \
                    ".......[OK]\n")
            else:
                print(
                    "VSPERF DID Not Installed Correctly , INSTALL IT AGAIN...........[Critical]\n")
        else:
            print(
                "VSPERF DID Not Installed Correctly , INSTALL IT AGAIN................[Critical]\n")
            break

def variable_from_test_config(aparameter):
    """This function can be use to read any configuration paramter from vsperf.conf"""
    read_cmd = 'cat ~/vsperf.conf | grep "{}"'.format(aparameter)
    read_cmd_output = str(DUT_CLIENT.execute(read_cmd)[1])
    print(read_cmd_output)
    if not read_cmd_output or '#' in read_cmd_output:
        return 0
    return read_cmd_output.split("=")[1].strip()


def get_results():
    ""

def run():
    if DUT_IP:
        host_connect()
    if not DUT_CLIENT:
        print('Failed to connect to DUT ...............[Critical]')
        sys.exit()
    else:
        upload_test_config_file()
        sanity_vnf_path()
        sanity_vsperf_check()
        run_vsperf_test()
