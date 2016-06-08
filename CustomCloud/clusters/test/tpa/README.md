This playbook sets up a 3 node cluster. It installs PostgreSQL
9.5 on the nodes. The repmgr packages are used to setup the standby nodes.
The repmgrd daemon gets configured appropriately to allow automatic
failover in case the primary goes down. The VMs are installed with
Ubuntu 16.04 LTS 64 bit (Xenial) distro.

1. Ensure that the pre-requisites have been installed appropriately
before doing anything else (python packages, virtualend, ansible)!

2. Provision the cluster instances

   ```
   (ansible-python) nikhils@ubuntu-xenial:~/2ndQ$cd TPA/CustomCloud

   utils/ansible-playbook platforms/aws/provision.yml \
       -e cluster=./clusters/test/tpa -vvvv
   ```

   The above command will use the contents of
   ```
   TPA/CustomCloud/clusters/test/tpa/config.yml
   ```
   to provision the instances. The first instance in this config.yml is tagged
   as "primary" and the other two will be tagged as "standby" instances. Kindly
   note the IP address of the "primary" instance as that is the IP where
   users will be able to connect to access PostgreSQL.

   On successful completion of the above command, 3 instances will have
   been provisioned. The inventory of the instances will be available as:

   ```
   (ansible-python) nikhils@ubuntu-xenial:~/2ndQ/TPA/CustomCloud$ cat clusters/test/tpa/inventory/00-TPA

   [tag_Name_TPA]
   52.90.44.83
   54.187.3.43
   54.194.62.203

   [tag_Name_TPA:vars]
   cluster_name=TPA
   ansible_user=ubuntu
   ansible_python_interpreter=/usr/bin/python2.7

   ```
   Obviously the IP addresses in your case will be different from the
   above sample output.

3. Ensure that SSH to these instances works

   The above provisioning activity creates ssh keys which are uploaded to these instances.

   ```
   (ansible-python) nikhils@ubuntu-xenial:~/2ndQ/TPA/CustomCloud/clusters/test/tpa$ ls
   config.yml  deploy.yml  id_rsa  id_rsa.pub  id_tpa  id_tpa.pub  inventory  README.md
   ```
   It also ensures that these keys are added locally via ssh-agent using ssh-add. If the
   keys are added properly, then SSH into all the 3 instances one by one and ensure that
   SSH works seamlessly. This step is very important to ensure that all the three
   instances are reachable over the network from your local machine

   ```
   (ansible-python) nikhils@ubuntu-xenial:~/2ndQ/TPA/CustomCloud$ ssh ubuntu@52.90.44.83

   (ansible-python) nikhils@ubuntu-xenial:~/2ndQ/TPA/CustomCloud$ ssh ubuntu@54.187.3.43

   (ansible-python) nikhils@ubuntu-xenial:~/2ndQ/TPA/CustomCloud$ ssh ubuntu@54.194.62.203
   ```

4. Carry out the actual software deploy

   After checking step 3, fire off the command to do the actual deployment on these instances
   ```
   (ansible-python) nikhils@ubuntu-xenial:~/2ndQ$cd TPA/CustomCloud

   utils/ansible-playbook -i clusters/test/tpa/inventory clusters/test/tpa/deploy.yml -e cluster=./clusters/test/tpa -vvvv

   ```
   If all the steps in the playbook are successfully deployed, then you will have a fully
   functional 3 instance cluster PostgreSQL 9.5 setup with automatic failover controlled by
   repmgr in place. You will now be able to access PostgreSQL on port 5432 using the
   "postgres" user on the "primary" IP address obtained in step 1 above.

5. Deprovision the resources

   This playbook provisions t2.small AWS instances and also provisions extra volumes. So,
   after carrying out your testing, please ensure that the instances are terminated if they
   are not needed further. Right now the additional volumes also need to be deleted
   manually from the AWS console. Here's the step to do the deprovisioning:

   ```
   (ansible-python) nikhils@ubuntu-xenial:~/2ndQ$cd TPA/CustomCloud

   utils/ansible-playbook -i clusters/test/tpa/inventory platforms/aws/deprovision.yml -e cluster=./clusters/test/tpa -vvvv
   ```

Please reach out to Nikhils, AMS, Haroon, The TPA team for any further queries/concerns/feedback.
