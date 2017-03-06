#!/usr/bin/python
import random
import subprocess
import re
import sys
import os

list_of_customers = []
list_of_all_used_ip = []

class Customer:
    owner = None
    cluster_name = None
    def __init__(self, owner):
        self.owner = owner

    def report(self):
        print "---------------------"
        print " Owner is ", self.owner
        print " cluster name is ", self.cluster_name
        print "---------------------"

def findUsedIps():
    grep = subprocess.Popen(['grep', '-Eor', '-w', '-h',
'[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}', '.'],
stdout=subprocess.PIPE)
    return grep.stdout.read().split('\n')

def createNewCluster(filename, new_owner, new_cluster_name, IP_range_low, IP_range_high):
    global list_of_customers

    print "Starting processing file:", filename
    print "new owner:", new_owner
    print "new cluster name:", new_cluster_name
    print "random range: [", IP_range_low, "," ,IP_range_high, "]"
    new_customer = Customer(filename)
    list_of_customers.append(new_customer)
    f_new = None
    f = None
    try:
        f = open(filename, 'r')
        f_new = open(filename[0:filename.index(".")]+"_test"+filename[filename.index("."):], 'w')
    except IOError:
        print "Error: File does not appear to exist."
        return None

    for line in f:
        new_line = line
        if "Owner" in line:
            new_customer.owner = line[line.index(":")+1:]
            new_line = line[:line.index(":")+1] +" "+ str(new_owner)
        if "cluster_name" in line:
            new_customer.cluster_name = line[line.index(":")+1:]
            new_line = line[:line.index(":")+1] + " \"" + str(new_cluster_name) + "\"\n"

        new_line = lineHasIp(new_line, new_customer, IP_range_low, IP_range_high)
        f_new.write(new_line)

    f.close()
    f_new.close()
    return None

def lineHasIp(line, new_customer, IP_range_low, IP_range_high):
    IP = None
    global list_of_all_used_ip
    new_line = line
    if "cidr_ip" not in line:
        if "." in line :
            if "/" in line:
                if "subnet" in line:
                    inital_text = line[:line.index("subnet")+8]
                    IP = line[line.index("subnet")+8:line.index("/")]
                    end_text = line[line.index("/"): ]
                else:
                    for i in line:
                        if i.isdigit():
                            index = line.index(i)
                            break

                    inital_text = line[:index]
                    IP = line[index:line.index("/")]
                    end_text = line[line.index("/"): ]
    if IP is not None:
        print "\t-----"
        print "\tIP to be changed:", IP
        IP_split = IP.split(".")
        IP_split[0] = 10
        IP_split[1] = 33
        randomness = random.randint(IP_range_low, IP_range_high)
        #IP = str(IP[0])+"."+str(IP[1])+"."+str(randomness)+"."+str(IP[3])
        IP = str(IP_split[0])+"."+str(IP_split[1])+"."+str(randomness)+"."+str(IP_split[3])
        found_good_one = True
        if IP in list_of_all_used_ip:
            randomness = random.randint(IP_range_low, IP_range_high)
            found_good_one = False

        while not found_good_one:
            randomness = random.randint(IP_range_low, IP_range_high)
            IP = str(IP_split[0])+"."+str(IP_split[1])+"."+str(randomness)+"."+str(IP_split[3])
            found_good_one = True
            if IP in list_of_all_used_ip:
                randomness = random.randint(IP_range_low, IP_range_high)
                found_good_one = False
        New_IP_Split = IP.split(".")

        if New_IP_Split[3]!= IP_split[3]:
            raise ValueError ("Something went wrong in the last octet!")

        print "\tnew IP generated:", IP
        new_line = inital_text+IP+end_text
    return new_line

def main():
    global list_of_customers, list_of_all_used_ip


    if '--help' in sys.argv[1:]:
        print "===================================="
        print "Welcome to config parser! here are the list of the arguments:"
        print "-Owner [owner name]: you can insert the name of the new owner"
        print "-cluster_name [cluster name]: you can insert the name of the new cluser"
        print "-IP_range [low] [high]: you can insert the range for your IP random generator"
        print "-i : input config file path"
        print "===================================="
        sys.exit()
    if '-Owner' in sys.argv[1:]:
        new_owner = sys.argv[sys.argv.index('-Owner') + 1]
    if '-cluster_name' in sys.argv[1:]:
        new_cluster_name = sys.argv[sys.argv.index('-cluster_name') + 1]
    if '-IP_range' in sys.argv[1:]:
        IP_range_low = int(sys.argv[sys.argv.index('-IP_range') + 1])
        IP_range_high = int(sys.argv[sys.argv.index('-IP_range') + 2])
    if '-i' in sys.argv[1:]:
        input_file = sys.argv[sys.argv.index('-i') + 1]


    list_of_all_used_ip = findUsedIps()
    print "starting list of all used IPs", list_of_all_used_ip
    print "======================================================"
    createNewCluster(input_file, new_owner, new_cluster_name, IP_range_low, IP_range_high)
    for customer in list_of_customers:
        customer.report()
    return 0

main()
