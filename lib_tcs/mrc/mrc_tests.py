#######################################################
# 
# This is the common library for MRC related test cases.
# This contains all the common functions required by most of the MRC TCs.
# 
# Test bed provisioning, configuration & orcehstration is done by framework lib.
# Executing tests concurrently on all cpu cores of all available test servers is
# done by framework lib.
#
# Installing test tools specific to MRC tests and common logging is provided
# by this library.
#
# TBD :
# 1). Check all required config values, else fail.
# 2). Include support for docker based REST API testing.
#
# MRC library is dependent on fabric tool and pp standard python external libraries.
# Makes life so much easier for spending the gray cells on test coverage.
#
######################################################

__all__ = []
import os
import sys
import logging
import glob
import time
import subprocess
from time import strftime, gmtime
import requests
import json
from requests.exceptions import ConnectionError
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
from fabric.context_managers import settings
from mrc_test_bed import deploy_test_vms
import BaseHTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
import cp_global
import mrc_common_utils
import pp

# MRC Test Suite related global values
#log_dir = 
#tc_dir = 
#report_dir = 
pass_cntr = 0
fail_cntr = 0
tcs_num = 0
mrc_log_name = ''
start_time = strftime("%Y-%m-%d-%H-%M", gmtime())

# Read the test setup details specfic to MRC test cases.
def init_mrc():
	# TBD : Move this to common framework lib and pass flags like mrc, unit etc.
	# Depending on flags make logging specific to that test option.
	logger = get_logger()

	# Phase 1: MRC Test bed/environment configuration validation.
	deploy_test_vms(logger)

	# Phase 2: We now have a test bed to execute MRC test cases.
	run_tests()

	# Phase 3: Test Suite execution report.
	report_mgmt_update()

	# Phase 4: Cleanup of test setup.
	#shiva_the_destructor()


# Common function to start execution of the MRC tests.
def run_tests():
	logger.info("MRC START: %s: MRC Test suite excution in progress.", start_time)
	tc_dir = os.getcwd() + "/tests/mrc_tcs/*.tc"
	
	# Get TC Statistic: count the number of '*.tc' config files in mrc/tests folder.
	if glob.glob(tc_dir):
		# Run all the TCs in the suite.
		if cp_global.runtest == []:
			mrc_tcs = glob.glob(tc_dir)
			global tcs_num
			tcs_num = len(mrc_tcs)
			logger.info("Total number of MRC TCs to execute is %s", len(mrc_tcs))
		# Run specific TCs, given at runtime.
		else:
			# Check for comma, separated values and then make a absolute 
			# paths to fio jobfiles.
			mrc_tcs = cp_global.runtest
			# Check if multiple TCs are given by comparing ',' in the string.
			#if mrc.tcs.find(',') != -1:
			#	for x in mrc.tcs.split(','):
			#		x = os.getcwd() + "/tests/mrc_tcs/" + x
			global tcs_num
			tcs_num = len(mrc_tcs)
			logger.info("Total number of MRC TCs to execute is %s", len(mrc_tcs))

		if cp_global.burstmode == 0:
			for tcs in mrc_tcs:
				tc_name = os.path.basename(tcs)
				logger.info("--------------------Executing TC: %s------------------" + "\n", tc_name)
				# run fio based MRC test cases. 
				# showconfig option is to do a dry run and not run.
				if cp_global.showconfig == 0:
					ret_fio = run_mrc_tcs(tcs)
				else:
					logger.info("Note: Doing a Dry run of MRC Test Suite, listing all config \
						 and global variables being and used tests to run.\n")
					logger.info("Exit after printing all the defaults and MRC tests.")

				logger.info("#--------------------------------------------------------------#")
		else:
			logger.info("Executing MRC TCs in parallel on available cpu cores.")
			burst_tcs(mrc_tcs)
	else:
		logger.error("Exit: No Testcases Or files with .tc extension at: %s", tc_dir)
		exit(1)

#########################################################################################
#
# PP is a python module which provides mechanism for parallel execution of python code on 
# SMP (systems with multiple processors or cores) and clusters (computers connected via network).
#
# The most simple and common way to write parallel applications for SMP computers is to use threads. 
# Although, it appears that if the application is computation-bound using 'thread' or 'threading' python 
# modules will not allow to run python byte-code in parallel. The reason is that python interpreter 
# uses GIL (Global Interpreter Lock) for internal bookkeeping. This lock allows to execute only 
# one python byte-code instruction at a time even on an SMP computer.
#
# PP module overcomes this limitation and provides a simple way to write parallel python applications. 
# Internally ppsmp  uses processes and IPC (Inter Process Communications) to organize parallel computations. 
# All the details and complexity of the latter are completely taken care of, and your application just 
# submits jobs and retrieves their results (the easiest way to write parallel applications).
#
# To make things even better, the software written with PP works in parallel even on many computers 
# connected via local network or Internet. Cross-platform portability and dynamic load-balancing allows 
# PP to parallelize computations efficiently even on heterogeneous and multi-platform clusters.
#
########################################################################################

def burst_tcs(all_tcs):
	# Using ppserver for clustered test execution is not a good idea.
	# Fabric and some inbuilt logic will do. CP framework will use pp only for
	# SMP test execution locally on all cpus.
	ppservers = ()

	# Creates jobserver with automatically detected number of workers
	# This will dynamically detect the ncpu on localhost and not hardcoded.
	# lscpu | grep -E '^Thread|^Core|^Socket|^CPU\('
	job_server = pp.Server(ppservers=ppservers)
	logger.info("Starting pp with %s workers for TCs", job_server.get_ncpus())

	# Submit n jobs with unique fio config file for TC execution. 
	# Execution starts as soon as one of the workers will become available
	#job1 = job_server.submit(run_mrc_tcs, ('tcs',))
	try:
		jobs = [(input, job_server.submit(run_mrc_tcs,(input,))) for input in all_tcs]
		#jobs = [(input, job_server.submit(run_mrc_tcs,(input,),(mrc_oracle,mrc_rest,get_logger,),())) for input in all_tcs]
	except:
		logger.info("FAILED PARALLLELELY")
	for input, job in jobs:
		print "Sum of primes below", input, "is", job()
	job_server.print_stats()
	#result = job1
	#job_stat = job_server.print_stats()
	#logger.info("Result of Job1:%s and stats:%s", result, job_stat)

# Common function to report the test suite execution.
# At present, this in mrc lib but should be common to all.
# This function uses simplehhtpserver to display the result.
# When we move to other framework like pytest, unitest, reporting can be borrowed from there.
def report_mgmt_update():
	report_dir = os.getcwd() + "/status_mgmt_report/MRC_test_run" + start_time
	logger.info("Report Test Execution on Intranet with file: %s", report_dir)
	try:
		with open('%s' % report_dir, "a") as log:
			log.write("MRC Test started at:%s" % (start_time))
			log.write("Total number of Test Cases executed:%s\n" % (tcs_num))
			log.write("Total number of MRC FAILED Cases: %s\n" % (fail_cntr))
			log.write("Total number of MRC PASSED cases: %s\n" % (pass_cntr))
			log.write("Log Location of MRC Test execution:%s\n\n" % (mrc_log_name))
	except:
		logger.error("Warn: Failed to Log test execution for Reporting.")
	finally:
		print("\n\n")
		logger.info("------------------ Execution Summary -------------------")
		logger.info("MRC Test started at:%s", start_time)
		logger.info("Total number of Test Cases executed:%s", tcs_num)
		logger.info("Total number of MRC PASSED Cases: %s", fail_cntr)
		logger.info("Total number of MRC FAILED cases: %s", pass_cntr)
		logger.info("Detailed log of this Run is at:%s", mrc_log_name)
		print("\n")
		log.close()

#	HandlerClass = SimpleHTTPRequestHandler
#	ServerClass  = BaseHTTPServer.HTTPServer
#	Protocol     = "HTTP/1.0"
#	port = 8000
#	server_address = ('127.0.0.1', port)
#	
#	HandlerClass.protocol_version = Protocol
#	httpd = ServerClass(server_address, HandlerClass)
#	
#	sa = httpd.socket.getsockname()
#	print "Serving HTTP on", sa[0], "port", sa[1], "..."
#	httpd.serve_forever()

# Common function to run fio and check it sucess/fail status.
def run_mrc_tcs(job_file):
	global fail_cntr, pass_cntr
	durun = cp_global.runtime
	fio_opts = "--output" + " FIO_op" + " --runtime " + durun
	fio_cmd = "fio " + job_file + " " + fio_opts
	logger.info("Executing FIO with following job file options: %s", fio_cmd)
	
	result = subprocess.call(fio_cmd, shell=True)
	# Check if Fio failed to run or not.
	if result != 0:
		logger.error("Failed FIO Job:%s, with return code: %s", fio_cmd, result)
		sys.exit(1)
	#try: subprocess.check_output(cmd)

	# As each run of FIO finished, we need to wait for 10 seconds to make sure
	# new MRC recommendation, get effected.
	logger.warn("Sleeping 10 seconds for MRC values to take effect.")
	time.sleep(1)

	# Calculate the estimated MRC for this fio jobfile.
	exptd_mrc = mrc_test_oracle(job_file)

	# This function will make a CP REST request to get the current MRC value.
	# The function return the mrc cache size value to caller.
	logger.info("Make CP MRC Rest call to get the current value.")
	actual_mrc = mrc_common_utils.get_json(logger, "mrc")
	logger.info("Following CP REST response recevied: %s", actual_mrc)

	logger.info("Comparing test computed MRC Vs current MRC value reported by CP REST.")
	# TBD: Below needs to be corrected.
	if exptd_mrc == actual_mrc:
		logger.info("TC PASS: Test computed MRC and CP REST value Do Not Match: %s", cp_global.abortfirst)
		fail_cntr += 1

		# TBD : We need to exit at first TC failure, as Default behavior.
		# The logic is otherwise, for now, for working out the burstmdoe.
		if cp_global.abortfirst == 1:
			logger.error("TC Failed, exiting. Please refer logs.")
			exit(1)
	else:
		logger.error("TC FAIL: Test computed MRC and CP REST value Do Not Match")
		pass_cntr += 1


# This function will read the blocksize of each of each fio job and then calculate
# the MRC for it. Average Bandwidth & IOPs Calculation, as follows:
# From Test Case doc : E.g., If 5 IOs and 4K BS and it takes 1 sec to complete then,
# 5*4K = 20k/s. 2. So, the recommended would be 4K block size & 4K + 15% cache size
# 3. Miss Ratio Curve for read, write should start from value 1 and should decends towards lower value 0
# 4. MRC graph should show the cache size
# This is a rough calculation and fail safe. Framework is automating what 200 MRC manual
# tests do for validation. The cache size validation is Not full proof and cannot be.
# But, it does give us 2 importants verifications. (1) The recomemended cache size is not
# less than the fio file written.
		
def mrc_test_oracle(job_file):

	logger.info("Test: Calculating estimated MRC cache size fio jobfile: %s.", job_file)

	avg_bw = from_fio_get("bw")
	avg_iops = from_fio_get("iops")
	#nblocks = 
	# TBD : Read blocksize from the fio config and calculate the MRC.
	# Each fio jobfile has its own associated mrc value.
	# We need to map each fio jobfile with its CP recommended values.
	return(1) # Amol Tester's validation method.

# Lessons from Stress, noise: To create an efficient program, It's important to
# close your open files as soon as possible: open the file, perform your operation, and close it.
# Don't leave it open for someone to spends days and filing dcpn.
def from_fio_get(strtomatch):
	#line = []
	with open('FIO_op', 'rt') as in_file:
		#line = in_file.read()
		for line in in_file:
			# bw (KB  /s): avg=16402.63
			if('bw (KB  /s)' in line and strtomatch == 'bw'):
				import re
				bw_val = re.findall('avg=', line)
				#print("LINE:%s", line)
				#bw_val = line.split(',')
				print("BW:%s", bw_val)
				return(bw_val)
			elif(strtomatch in line and strtomatch == 'iops'):
				iops_val = line.split('iops=')
	in_file.close()

# This function will make a CP REST request to get the current MRC value.
# The function return the mrc value to caller.
def mrc_rest():
	logger.info("Make CP MRC Rest call to get the current value.")

	json_val = mrc_common_utils.get_json(logger, "mrc")
	logger.info("Following CP MRC response recevied: %s", json_val)
	exit(1)

# JIRA TC set execute and complete status for mrc TCs
# Use of zephyr API. 
#def jira_update():
	# Automate the boring stuff like execute and run.


# Setup logging for MRC test cases. Logging is written to a predefined file location.
# Currently, logging happens at the test suite level.
# TBD : TC Level logging and process level logging.
def get_logger():

	global logger
	path = os.getcwd() + "/logs_tcs/mrc_logs/"
	#from logging.handlers import TimedRotatingFileHandler
	#logger = TimedRotatingFileHandler(LOG_FILE, when=LOG_ROTATION_TIME)
	logger = logging.getLogger(__name__)
	logger.setLevel(logging.INFO)

	# Unique name for each run of mrc tests.
	nowtime = strftime("%Y-%m-%d-%H-%M", gmtime())
	path = path + "MRC-Tests" + nowtime + ".log"
	global mrc_log_name
	mrc_log_name = path
	handler = logging.FileHandler(path)
	handler.setLevel(logging.INFO)

	# create a logging format
	formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	handler.setFormatter(formatter)

	# add the handlers to the logger
	logger.addHandler(handler)

	consoleHandler = logging.StreamHandler()
	consoleHandler.setFormatter(formatter)
	logger.addHandler(consoleHandler)
	
	logger.info("Setting up and Returning MRC logger")
	return logger
