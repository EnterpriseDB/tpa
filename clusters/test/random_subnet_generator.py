#!/usr/bin/python
import random
import subprocess

# finds used id addresses from the current cluster (clusters/test/)

def findUsedIps():
    grep = subprocess.Popen(['grep', '-Eor', '-w', '-h', '[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}', '.'], stdout=subprocess.PIPE)
    return grep.stdout.read().split('\n')

# takes number of ip addresses that will be created
# and used ip addresses list as inputs
# iterates until reaching the required numbers of ips
# compares the random created ips with existing ones
# if they don't overlap adds the random ip
# to the new ip addresses list

def ipGenerator(number, used):
    ip_list = []
    while True:
        ip = "10.33."
        ip += ".".join(map(str, (random.randint(0, 255)
                                for _ in range(2))))
        if ip in used:
            continue
        ip_list.append(ip)
        if (len(ip_list) == number):
            break
    print ip_list

def main():
    numberOfIpAddresses = input("Enter the number of IP addresses you need: ")
    used_ip_list = findUsedIps()
    ipGenerator(numberOfIpAddresses, used_ip_list)

main()

