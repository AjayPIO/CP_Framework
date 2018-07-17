###################################################################
#
# This is the usuability interface for the CP Automation framework.
# There is no major requirements to get started and the framework
# setups or reuses whatever without failing fast. The process of running 
# test suites/cases should be painless and not cumbersome.
#
# It should be easy to add/intergrate new test suite, the framework in all 
# its simplicity, is just a wrapper to run almost all programs and test tools.
# For example : Look at CP unit test integration. 
#
# CP framework will abstract all the test setup and running in parallel or on
# remote seamlessly and mostly transparent to the user. 
# For Example : Look at MRC integration test suite.
#
##################################################################

# importing the required modules
#__all__ = []
import os
import argparse
from argparse import RawTextHelpFormatter
import sys

# Test Framework Libraries
from lib_tcs.unit import unit_tests
from lib_tcs.mrc import mrc_tests
import cp_global
global tclist

# There are legacy 2.7 test suites and the framework needs to support 2.7 and python3.
# There are libraries to do the above, like 2to3 etc. Presently, the requirements are less andlow priority.
#isPython3 =  sys.version_info[:2] >= (3,0)
#
#if isPython3:
#	config = configparser.ConfigParser()
#	request.data = data
#	import email.generator as mimetools
#	import urllib.request as urllib2
#	from urllib.parse import urlencode
#else:
#	config = ConfigParser.SafeConfigParser()
#	request.add_data(data)
#	import mimetools
#	import urllib2
#	from urllib import urlencode

# Why am i spending so much time on help messages ? USUABILITY
# It should be easy to run by everyone and needs no human dependency to run it.
# For the sake of usuability, READMEs are great but humans dont read.
# If there are barrier to get started with the tool, humana loose interest to something 'simpler'
# Most of the frameworks and tools grow too complex, over time, to be usuable and involve learning curve.
#
# All test framework need to be friendly enough and itntelligent enough to just get the tests running.
# Hence, just taking user input as --unit and running all unit tests is a design consideration.

def main():
	# Lets figure out what needs to be done. What testing needs to be done.
	parser = argparse.ArgumentParser(description = "CP Automation test manager, At your service !", \
				formatter_class=RawTextHelpFormatter, add_help=True)
	parser.add_argument("--mrc", help="Run integration MRC test cases. Checkout latest git tests and run selected cases. \
				\nNOTE : Run --mrc --showconfig to Get You Started, with a dry run.\n\n", action="store_true")
	parser.add_argument("--planning", help="Run planning test suite with FIO jobs/IO & validate against CP REST. \
				\nNOTE : Run --planning --showconfig to Get You Started, with a dry run.\n\n", action="store_true")
	parser.add_argument("-u", "--unit", help = "This option will Run all CP Unit tests. \
				\nThe latest git unit test code is checked out. Use --runtests, --hosts & --duration \
				\nNOTE : Run --unit --showconfig to Get You Started, with a dry run.\n", action="store_true")
	parser.add_argument("--scalability", help = "CP scalibility tests are run using Locust tool. \
				\nUse this option for stress tests and to setup test bed.\n", action="store_true")
	parser.add_argument("-rcm", "--recommendations", help="TBD: Include recommendations, benefits TCs here.\n", action="store_true")
	parser.add_argument("-p", "--performance", help="TBD: Run performance tests\n\n", action="store_true")
	parser.add_argument("-sc", "--showconfig", help="DryRun: Show the default config values being used for the test.\n", action="store_true")
	parser.add_argument("-b", "--burstmode", help="This is scale-in/out framework mode running tests concurrently on localhost \
				\nand distributing among all test slaves. This option is experimental and optional. \
				\nNOTE: Unit component tests are good candidates for this option.\n", action="store_true")
	parser.add_argument("-f", "--failfirst", help="By Default, the framework will abort at the first failure. \
				\nUse this flag to ignore TC failures and execute entire suite.\n\n", action="store_true")
	parser.add_argument("-s", "--showTC", help="TBD: Describe the given TCs and its coverage areas.\n", action="store_true")
	parser.add_argument("-n", "--newsetup", help="TBD: Create new setup for the test suite as specified in config file. \
				\nDEFAULT is to use the existing setup. The framework will discover and populate \
				\nrequired infra info from host.", action="store_true")
	parser.add_argument("-r", "--runtests", help="This option helps to run specific TCs, range of TCs and All TCs. \
				\nEx: --runtest all(Default), Or --runtest TC1,TC2,TC3\n", \
				action='append', dest='listoftests', default=[])
	parser.add_argument("-d", "--duration", help="TBD: Specify the duration of test run. \
				\nEx: --duration 12mintues, --duration 1hour, --duration 1day\n\n", action="store_true")

	args = parser.parse_args()

	# Set the global, these are required to make intelligent choices in life.
	# TBD : Another file is an overkill(mgmt_hpy). Lets update the test suite config file
	# with the runtime options.
	if args.failfirst:
		cp_global.abortfirst = 1
	elif args.burstmode:
		cp_global.burstmode = 1
	elif args.showconfig and args.mrc:
		# This option does a dry run on the test suite/s choosen to run.
		# This helps to validate the test beds, test setups and cases to run.
		# List all the config files with values, test bed infra details, test cases to run.
		cp_global.showconfig = 1
	elif args.failfirst and args.burstmode:
		cp_global.abortfirst = 1
		cp_global.burstmode = 1
	elif args.listoftests:
		cp_global.runtest = args.listoftests
	else:
		print("Using all defaults for this test run.\n")
	# TBD: elif duration: enforcing the same format as FIO expects.
	# Calling Test Suites depending on type of argument
	if args.unit:
		cp_global.abortfirst = 1
		unit_tests.run()
	elif args.mrc:
		# Call MRC Test Suite for exeuction.
		print("\nRunning MRC Test Suite.\n")
		mrc_tests.init_mrc()
	elif args.planning:
		print("\nTBD: Running CP Planning Test Suite.\n")
		# TBD: Call planning test suite.
	elif args.unit:
		print("\nTBD: Running CP Unit Test Suite.\n")
		# TBD: Call Unit Test Suite.
	elif args.scalability:
		print ("TBD: Call Locust.io to do CP scalibility testing.\n")
	elif args.recommendations:
		print ("TBD: Include recommendations, benefits TCs.\n")
	elif args.performance:
		print ("TBD: Include CP Performance tests.\n")
	else: 
		if len(sys.argv)==1:
			print ("ExitGreat, nothing to do. But,let the dumb machines work.")
			parser.print_help(sys.stderr)
			exit()

if __name__ == "__main__":
	# calling the main function
	main()

