This playbook sets up a 3 node cluster. It installs PostgreSQL
9.6 on the nodes. The repmgr packages are used to setup the standby nodes.
The repmgrd daemon gets configured appropriately to allow automatic
failover in case the primary goes down. The VMs are installed with
Ubuntu 16.04 LTS 64 bit (Xenial) distro.

1. Ensure that the pre-requisites have been installed appropriately
before doing anything else (python packages, virtualend, ansible)!

2. Provision the cluster instances

   ```
   (ansible-python) nikhils@ubuntu-xenial:~/2ndQ$cd TPA/CustomCloud
   
   utils/provision test/tpa -vvvv
   ```

   The above command will use the contents of
   ```
   TPA/CustomCloud/clusters/test/tpa/config.yml
   ```
   On successful completion of the above command, 3 instances will have
   been provisioned. The inventory of the instances will be available as:

   ```
   (ansible-python) nikhils@ubuntu-xenial:~/2ndQ/TPA/CustomCloud$ cat clusters/test/tpa/inventory/00-TPA
   [tag_Cluster_TPA]
   54.206.117.89 node=1 db="primary" role="[]"
   54.206.16.159 node=2 db="standby" role="[]"
   54.206.45.65 node=3 db="standby" role="[]"

   [tag_Cluster_TPA:vars]
   cluster_name=TPA
   ansible_user=ubuntu
   ansible_python_interpreter=/usr/bin/python2.7
   serviceid=B67891
   customerid=A12345
   ansible_ssh_private_key_file="clusters/test/tpa/id_tpa"
   ansible_ssh_common_args="-o UserKnownHostsFile='clusters/test/tpa/known_hosts'" 
   
   ```
   Obviously the IP addresses in your case will be different from the
   above sample output.

   **NOTE 1** Sometimes you might get the following error:
   ```
   "msg": "boto required for this module"
   ```
   The above can be resolved by explicitly adding the virtualenv site-packages directory to PYTHONPATH.
   ```
   export PYTHONPATH=/home/ubuntu/ansible-python/lib/python2.7/site-packages:$PYTHONPATH
   ```
   
3. Carry out the actual software deploy

   **NOTE 1** If you want to assign elastic IP to the primary, then edit clusters/test/tpa/config.yml and change the entry
   ```
   assign_eip: false
   ```
   to 
   ```
   assign_eip: true
   ```
   
   **NOTE 2** The default config.yml/deploy.yml sets up a 1 master, 2 standby TPA cluster with automatic failover using repmgr in place. If you want to create a TPA cluster with its dedicated **barman** instance, then edit clusters/test/tpa/config.yml. You can add a new fourth instance here for the barman instance or just for testing, you can even convert the standby instance to a barman instance. If you add a fourth instance, be careful about specifying subnet and other values appropriately. For testing purposes, you can do the below
   ```
   tags:
        db: standby
        node: 3
   ```
   change the above to:
   ```
   tags:
        db: barman
        node: 3
   ```
   for the second standby listing. Or if not, feel free to add a fourth instance in the config.yml as appropriate.
   
   After taking care of additional requirements if any from above two notes, fire off the command to do the actual deployment on these instances
   ```
   (ansible-python) nikhils@ubuntu-xenial:~/2ndQ$cd TPA/CustomCloud

   utils/deploy test/tpa -vvvv

   ```
   If all the steps in the playbook are successfully deployed, then you will have a fully
   functional 3 instance cluster PostgreSQL 9.5 setup with automatic failover controlled by
   repmgr in place. You will now be able to access PostgreSQL on port 5432 using the
   "postgres" user on the "primary" IP address obtained in step 1 above. 
    

5. Deprovision the resources

   This playbook provisions t2.small AWS instances and also provisions extra volumes. So,
   after carrying out your testing, please ensure that the instances are terminated if they
   are not needed further. Here's the step to do the deprovisioning:

   ```
   (ansible-python) nikhils@ubuntu-xenial:~/2ndQ$cd TPA/CustomCloud

   utils/deprovision test/tpa -vvvv
   ```

Please reach out to Nikhils, AMS, Haroon, The TPA team for any further queries/concerns/feedback.
