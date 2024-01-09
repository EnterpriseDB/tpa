#!/bin/bash


	##########################
	# Setup build environment
	##########################
	SetupEnv(){
	  echo "Install Requirements"
	  sudo apt-get -y install python3-pip libpq-dev python3-dev
	  sudo apt install python3.8-venv
	  sudo python3 -m pip install --upgrade pip
	  sudo python3 -m pip install tox
	}


	##################
	# Generate reports
	##################
	GenerateReports(){
	
	echo "Create Coverage report"
	python3 -m tox -e py38-test
	}


	########
	# Main
	########
	SetupEnv
	GenerateReports
