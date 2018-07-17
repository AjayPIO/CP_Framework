###########################################################################
#
# All great frameworks abstract learning new technologies and concentrate
# on logic. How fabric does its magic should be part of framework and
# abstracted/encapsulated from end users.
#
# We are trying to achieve this with updating/reading common csv config file.
# The end user thus only provide hostnames in config and need/required to know
# how fabric uses these hosts and connections made.
#
# The config driven framework approach in this manner will abstract other tools/tech
# too. The framework will read the config file for test VMs and then update fabric
# with those details.
#
# This also makes the framework portable and hetrogenous.getting-python-fabric-setup-in-windows
##########################################################################

import os
import sys
import random
from ConfigParser import SafeConfigParser
from fabric.api import *
from fabric.api import run, env, hosts, roles, execute
from fabric.contrib.files import append, exists
from fabric.decorators import hosts, roles, runs_once
#import cp_automation.settings as testinfra_settings

# The GLobals
# the servers where the commands are executed
global logger
env.host_string = ['cptest-host1', 'cptest-host2']
env.hosts = ['user@host1:1234', 'user@host2:2345']
env.username = "root"
GIT_REPO_URL = "https://github.com/CacheboxInc/naruto/tree/RELEASE/naruto/QA"
cwd = os.getcwd()
cwd = cwd + "/lib_tcs/mrc/"


# env.project_dir = '%s%s/' % (env.code_dir, dj_settings.PROJECT_NAME,)
# env.package_dir = '%s%s/' % (env.project_dir, dj_settings.PACKAGE_MODULE,)
# env.project_git_uri = 'git@github.com:some-user/my-project.git'
# env.config_dir = '%sconfig/generated/' % env.project_dir
# env.log_dir = '%slogs/' % env.project_dir

# Purpose : Fabric environmental variable setup 
#def set_env(config, version_tag=None):
## When setting this inside a function. Using host_string as workaround
#config_dict = get_config(config)
#env.hosts = [config_dict['HOST_NAME'], ]
#env.host_string = config_dict['HOST_NAME']
#
#env.project_name = config_dict['TEST_NAME']
#env.project_dir = posixpath.join('/srv/images/', env.project_name)
#env.use_ssh_config = True
#
#env.image_name = config_dict['IMAGE'].split(':')[0]
#env.base_image_name = env.image_name + '_base'
#env.version_tag = version_tag
#
#env.build_dir = '/srv/build'
#env.local_path = os.path.dirname(__file__) 


# Install packes on servers as required or make a similar one for yoour requirements.
# Ex : CP scalibility testing depends on locust.io and that too can be installed on some
# remote test servers.
apt_packages = [
	#TODO: try to get as many of these as possible in requirements.txt
	# NOTE : Simply mention the tools and the framework can install on test servers.
	'wget'
	'FIO'
	'sysbench'
	'Vmmark'
	'Conf'
	'git',
	'ntp',
	'nginx',
	'python-pip',
	'python-virtualenv',
	'postgresql',
	#TODO: try to get as many of these as possible in requirements.txt
]

############################################################
#
# Housekeeping : It is interesting if all the servers are doing different things
# much like the production. Fabric gives us that flexibility and scaled out testing.
# 
# 1). Install anything(programs, test tools, programs etc) on any servers as on Local machine.
# 2). Send and run different commands and test tools on all test servers.
# 3). Collect/copy logs to central place and analysis and reporting.
# 4). Parallel remote execution support.
# 5). Fabric is an independent tool and No need for learning another language.
#
###########################################################

def pack():
	# build the package
	local('python setup.py sdist --formats=gztar', capture=False)

#@parallel
def install_requirements():
	# CD into mrc directory to find the requirement.txt, specific to MRC tests.
	with lcd(cwd):
		logger.info("Pip install test requiements and tool setups.")
		res = local("pip install -r requirements.txt")
		if res.failed:
			logger.critical("Failed pip install requirements from: %s", cwd)

		if is_tool('fio') is None:
			fio_install()
		else:
			logger.warn("Skipping Install, FIO is already installed.")


# Check tools exist before installing them.
def is_tool(name):
    """Check whether `name` is on PATH."""
    from distutils.spawn import find_executable
    return find_executable(name) is not None

# Module Purpose :
# 1). Use this module to install test tools like FIO, sysbench, VMmark; Locally or remote host.
# 2). Use this common function locally, remotely to checkout latest github codes.
# 3). pass a different configration file to deploy for automating setup and cleanup from test servers.

def deploy_test_vms(logs):
	global logger 
	logger = logs

	# Create CP framework required directories, on all test hosts.
	# cptest_dir = "/cp_automation/" + env.host_string[0]
	# with settings(host_string='cp-test-vm1'):

	# Validate the MRC test setup given to run the suite.
	chk_config()
	# Check if the existing test VMs are operational.
	test_vms_alive()
	logger.info('Install all required framework libraries and tools on local & remote test servers.')
	install_requirements()

	logger.info("Checkout Latest test framework code on all test hosts")
	get_latest_source()

# Check if all required confi parameter
def chk_config():

	# Read the test setup details specfic to MRC test cases.
	# if not os.path.exists(path): createConfig(path)
	config = SafeConfigParser()
	cwd = os.getcwd()

	conf_file = cwd + "/conf_tcs/mrc_conf/mrc_setup.conf"
	logger.info("Checking and validating the test infra mentioned in MRC config:%s", conf_file)
	try:
		config.read(conf_file)
		for section_name in config.sections():
			logger.info('%s MRC Conf section exists: %s' % (section_name, config.has_section(section_name)))
			for name, value in config.items(section_name):
				#logger.info('Present : %s' % (config.has_option(name, value)))
				logger.info("'%s' = '%s'" % (name, value))

	except config.ParsingError:
		logger.error ("Failed to parse the MRC test setup conf::s", conf_file)

	# TBD : Check for the required config parameter values else exit.
	try:
		testvms = config.get('hosts', 'test_slaves')
		logger.info("Starting MRC tests on following test machines:%s", testvms)
	except:
		logger.critical("EXIT: Missing test hosts details from config file:%s.\n", cwd)
		exit(1)

# Purpose:
# Perform check on given test vms/hosts in config. 
# Perform check if ssh connectivity is working by firing commands.
#@hosts('HOST1')
#@with_settings(warn_only=True)
def test_vms_alive():
	#logger = log
	logger.info("Checking if given test VMs are alive and reachable.")
	
	with settings(warn_only=True):
		# local("ssh %s" % env.host_string[0])
		res = local('uptime')
		if res.failed:
			logger.critical("Killing Tests, as Host printing this message is down. Huh!")
			abort('Aborting at Anamoly!')

	logger.info("Checking All REMOTE Test VMs as alive and reachable.")

#	with settings(warn_only=True, host_string='CP_test_VM'):
#		# TBD : Need to be OS independent and cater to all. Cant just uptime.
#		run('uptime')
#		if run('uptime').failed:
#			logger.critical("Failed to reach Remote Test Servers.")
#			abort('No Test Slaves to Work with')
#	try:
#		with settings(warn_only=True):
#			env.parallel=True
#			execute(uptime)
#	except Exception as e:
#		logger.info(e)

# Purpose : Common function to Install FIO on all choosen test servers(local, remote).
# This function calls a bash fio install script for easy installation.
def fio_install():
	tools_cwd = cwd + "tools/" 
	logger.info("Installing FIO on choosen hosts: %s\n", tools_cwd)
	local(fio_install)
	is_tool(fio)
	try:
		tools_cwd = tools_cwd + "SUCCESS.fio.install"
		f = open(tools_cwd)
		f.close()
	except IOError:
		logger.critical('Failed FIO installation.\n')
		exit(1)

	logger.info("FIO installed Successfully.\n")

# As a practise, we should refrain from remotely coyping local script changes, but checkout from git.
# It should be encouraged to checkout all test script from PIOgithub for each test run(TBD : Or optional 
# framework can check if a checkout of test code is required/needed.)
#@parallel
def get_latest_source():
	# Look for the .git hidden folder to check whether the repo has already been cloned on test server.
	with lcd(cwd):
		logger.info("Checking out the latest Testframework code from git url:%s", GIT_REPO_URL)
		#local('git clone %s letsencrypt'% GIT_REPO_URL)

		# Copies local tarball of repo to remote
		#put(local_path='cp_test_framework.tar.gz', remote_path='')
		#run('tar xzf le.tar.gz')
		return()

# Install all packages mentioned above, in parallel, to save build-test time.
# TBD : yum, and other install utilities can be expanded as below.
@parallel
def install_apt():
	logger.info("CPFabric: Updates and installs Apt dependencies for CP test framework.\n")
	try:
		sudo('apt-get update')
		sudo('apt-get upgrade')
		sudo('apt-get install -f %s' % ' '.join(apt_packages))
		logger.info( green( ' --> host %s can be reachable '%host))
	except:
		logger.info("CPFabric:Fail: MRC test setup failed on test servers.")

# Purpose : Install pip instal utility on all the test servers.
@parallel
def install_pip():
	logger.info("Fabric:Installs the PIP requirements for this project.")
	try:
		with cd(env.pip_dir):
			sudo('pip install -r %srequirements.txt' % env.project_dir)
	except:
		logger.info("CPFabric: Failed to install pip on host %s"%host)

# Distributed test cleanup, sounds expensive! Well, lot of filth surfaces during test runs.
# We leave our toilet seats up, is it up or down.
# Purpose : Clean my tests shit up, before ending the run.
def shiva_the_destroyer():
	#Remove all directories, databases, etc. associated with the application.
	run('rm -Rf %(path)s' % env)
	run('rm -Rf %(log_path)s' % env)
	run('dropdb %(project_name)s' % env)
	run('dropuser %(project_name)s' % env)
	sudo('rm %(apache_config_path)s' % env)
	local('find -name "*.pyc" | xargs rm -f')
	local('find -name .cp_fio | xargs rm -f')
	local('find -name .CP_Store | xargs rm -f')  # Created by OSX
	local('find -name ._DS_Store | xargs rm -f') # Created by OSX
	local('find -name "._*.*" | xargs rm -f')    # E.g. created by Caret
	local('rm -f .coverage.*')
	local('rm -rf build')
	local('rm -rf dist')

	with lcd(path.dirname(__file__)):
		local('python setup.py clean --all')
	
	# reboot()

def uptime():
	run('uptime')
	run('rm -Rf %(path)s' % env)

# TBD : Our present approach will help in doing interesting vmoperations, in interesting configurations.
# One can define to trigger snapshot on All or a subset of VMs and then in parallel run clone.
#def svmotion():
#def snapshot():
#def clone():
###########################################################################
