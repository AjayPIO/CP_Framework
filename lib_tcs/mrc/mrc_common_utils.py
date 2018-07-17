#####################################################
#
# This is a collection of common library functions.
# These are presently specific to MRC but should be moved out to
# Framework common_utils lib. All of the test suites should have a 
# common_utils lib. These should either inherit or extend framework
# comon_utils. This will ensure that only suite specific functions
# are part of their common_utils. 
# Framework common_utils should contain all functions common to
# all test suites.
#
####################################################
import requests
import json
from requests import ReadTimeout, ConnectTimeout, HTTPError, Timeout, ConnectionError
import os
from ConfigParser import SafeConfigParser
import sys

global logger
# Purpose : Return the current monitoring status of given vmdk.
# This function will figure out the ds_uuid, vmdk_uuid for the ease of 
# only calling the function with vmdk name.
# Inputs: 1). name of the vmdk to set/get monitoring information.
# 2). monitoring_op: Allowed flags: STATUS, ENABLE, DISABLE
def ret_monitoring_status(vmdk_name, mon_op):
	#vmdk_uuid
	#ds_uuid
	#test_obj = DaemonTest(URL)
	if (mon_op == "status"):
		data = {
			"vmdk_uuid" : vmdk_uuid,
			"ds_uuid"   : ds_uuid
		} 
		mon_stat = test_obj.get(data, MONITOR_URL, test_get_monitoring_status.__name__)
		return mon_stat
	elif (mon_op == "enable"):
		data = {
			"vmdk_uuid" : vmdk_uuid,
			"ds_uuid"   : ds_uuid,
			"monitoring": True
			}
		mon_stat = test_obj.put(data, MONITOR_URL, test_enable_monitoring.__name__)
		return mon_stat
	else (mon_op == "disable"):
		data = {
			"vmdk_uuid" : vmdk_uuid,
			"ds_uuid"   : ds_uuid,
			"monitoring": False
			}
		mon_stat = test_obj.put(data, MONITOR_URL, test_disable_monitoring.__name__)
		return mon_stat



# Return the uri for request url to get mrc value of interest.
# This function takes a vmname and returns the defined key-value pair for each of the present
# vmdk attached on that vm.
# TBD : Needs to move to framework common.utils.
# Expected argument, test suite keyword like mrc, unit etc.
# Return the value of config key.
def get_json(logr, suite_name):
	# Read the config file and populate the link for request.
	# Read the test setup details specfic to MRC test cases.
	global logger
	logger = logr
	config = SafeConfigParser()
	cwd = os.getcwd()
	conf_file = cwd + "/conf_tcs/mrc_conf/mrc_setup.conf"
	logger.info("Checking and validating the test infra mentioned in MRC config:%s", conf_file)
	try:
		config.read(conf_file)
	except config.ParsingError:
		logger.error ("Failed to parse the MRC test setup conf::s", conf_file)
	
	# Return required config parameter values else exit.
	# Depending on the test suite, return the url expected for rest request.
	if(suite_name == 'mrc'):
		logger.info("Create MRC url from the config file values.")
		try:
			app_ip = config.get('vm', 'appliance_ip')
			vm_id = config.get('vm', 'vm_uuid')
			vcntr_ip = config.get('vm', 'vcenter_ip')
			base_url = config.get('vm', 'mrc_base_url')
			mrc_url = base_url + 'vmdk?vm_uuid=%s&level=1&vcenter_ip=%s' % (vm_id, vcntr_ip)
			# clus_id = config.get('vm', 'cluster_id')
			# clus_name = config.get('vm', 'cluster_name')
		except:
			logger.critical("EXIT: Missing test hosts details from config file:%s.\n", conf_file)
			exit(1)

		got_json = get(mrc_url)
		return(got_json)

	elif(suite_name == 'planning'):
		logger.info("Fetch Desired Planning results.\n")
		return(1)
	elif(suite_name == 'logs'):
		logger.info("Download and save CP logs from the dashboard.\n")
		return(1)
	else:
		logger.info("This functions without matching keyword returns baseurl.")
		cp_base_url = config.get()


# This is the common framework requests.get function.
# Given any URL, this function does a check of the following for prosterity :
# requests.exceptions.Timeout: : set up for a retry loop. Our test infra is slow.
# requests.exceptions.TooManyRedirects: CP test URL was bad and try a different one.
# requests.exceptions.HTTPError: check for any httperror.
# response code to 200 : Heh, the whole Cp unit testing.
# All these checks are important because we know what exactly failed, instead of 
# saying something failed. As a common requirement, this should be in the common
# framework libs. Being specific saves so much time for everyone.
def get(get_url):
	logger.info("Calling CP REST GET for MRC:%s",get_url)
	try:
		# TBD : Need to get in the SSLError here.
		# Need to know is HTTP/HTTPS both are allowed.
		# To check a hosts SSL certificate, you can use the verify argument:
		# cafile = cacert.pem # http://appliance_ip/ca/cacert.pem
		# r = requests.get(url, verify=cafile)
		# r = requests.get(get_url, timeout=10, verify=False)
		r = requests.get("https://10.10.13.34:443/mrc/vmdk?vm_uuid=1010885_421fd73dae628942f718a4bdb7c05f1e_MRC18-01&level=1&vcenter_ip=10.10.8.85", verify = False, timeout=5)
		mrc_response=json.loads(r.text)
		json_mrc= mrc_response["data"]["1010885_6000C29780a2bc024b8d14ff84f055c3_MRC18-01"]["ioa_stats"]["recommendation"]["cache_size"]
		r.raise_for_status()

	# hey do this and get out : 
	# except (ConnectTimeout, HTTPError, ReadTimeout, Timeout, ConnectionError):
	except requests.exceptions.Timeout as terr:
    		# Maybe set up for a retry, or continue in a retry loop
		logger.error("Error: CP REST Timeout Exception:\n%s", terr)
		sys.exit(1)
	except requests.exceptions.TooManyRedirects as derr:
		logger.error("Error: CP Rest request failed with too many redirects:\n%s", derr)
		sys.exit(1)
	except requests.exceptions.HTTPError as herr:
		logger.error("Error: CP Rest request failed with HTTPError:\n%s", herr)
		sys.exit(1)
	except requests.exceptions.ConnectionError as errc:
		logger.error("Error CP Request failed with Connectionerror:\n%s", errc)
		sys.exit(1)
		# Given test CP URL was bad and try a different one
	except requests.exceptions.RequestException as e:
		# Something bad is happening, Lets blame it on DP and bail.
		logger.error("Exit: Uncaught REST request Error, Get human help:\n%s", e)
		sys.exit(1)

	logger.info("CP REST GET Validated for 200 status_code, timeout, redirects & Connection Errors.")
	return(json_mrc)

# Download debug logs (zip)
def download_cp_logs(self):
	get_logs_url = get_url("logs")
	res = get(get_logs_url)
	rc = res.getcode()
	data = res.read()
	logger.debug(dir(res))
	logger.debug(get_logs_url)
	logger.debug(rc)
	assertEqual(res.getcode(), 200)

	with open("pio_cp_logs.zip", "w") as fd:
		fd.write(str(data))
