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

   **NOTE 1** Sometimes you might get the following error:
   ```
   "msg": "boto required for this module"
   ```
   The above can be resolved by explicitly adding the virtualenv site-packages directory to PYTHONPATH.
   ```
   export PYTHONPATH=/home/ubuntu/ansible-python/lib/python2.7/site-packages:$PYTHONPATH
   ```
   
   **NOTE 2** Sometimes you might get the following errors:
   ```
   loop_var = result._task.loop_control.get('loop_var') or 'item'
   AttributeError: 'LoopControl' object has no attribute 'get'

   or
   
   fatal: [localhost]: FAILED! => {"failed": true, "msg": "'r' is undefined"}
   ```
   
   The above can be solved by checking out a specific commit tag of Upstream Ansible which is known to
   work ok:
   
   ```
   cd /path/to/upstream_ansible_dir
   git checkout c06884eff03ad133b83a27c2839055a65f669d36
   ```
   
3. Ensure that SSH to these instances works

   The above provisioning activity creates ssh keys which are uploaded to these instances.

   ```
   (ansible-python) nikhils@ubuntu-xenial:~/2ndQ/TPA/CustomCloud/clusters/test/tpa$ ls
   config.yml  deploy.yml  id_rsa  id_rsa.pub  id_tpa  id_tpa.pub  inventory  README.md
   ```
   It also ensures that these keys are added locally via ssh-agent using ssh-add. If the
   keys are added properly, then SSH into all the 3 instances one by one and ensure that
   SSH works seamlessly. This step is very **important** to ensure that all the three
   instances are reachable over the network from your local machine. 
   
   **NOTE 1** If you get issues accessing via ssh, then manually add the keys into your .ssh
   or using ssh-add.

   ```
   (ansible-python) nikhils@ubuntu-xenial:~/2ndQ/TPA/CustomCloud$ ssh ubuntu@52.90.44.83

   (ansible-python) nikhils@ubuntu-xenial:~/2ndQ/TPA/CustomCloud$ ssh ubuntu@54.187.3.43

   (ansible-python) nikhils@ubuntu-xenial:~/2ndQ/TPA/CustomCloud$ ssh ubuntu@54.194.62.203
   ```

4. Carry out the actual software deploy

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
   
   After checking step 3, and taking care of additional requirements if any from above three notes, fire off the command to do the actual deployment on these instances
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
