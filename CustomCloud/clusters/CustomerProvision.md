TPA Customer Provisioning Process
=================================

For the first few releases, 2ndQuadrant will provision the clusters on behalf of the customers.
Hence, we need to get few important pieces of information from the customers:

### Instance size requirements
==============================

  The customer needs to indicate what kind of instance (t2.large, m3.xlarge etc) is required in the
  deployment. This depends on their computing and storage requirements. The postgresql and barman
  directories are part of an additional volume (we create an ext4 FS on this volume and then it gets
  mounted at /var/lib/postgresql or /var/lib/barman as appropriate). We can recommended suitable 
  defaults for this as well.
  
### Cluster specific requirements
==================================

  The customer needs to indicate if they want HA in place. We assume this will be case and will be
  enabled by default. The customer needs to indicate if they want an exclusive barman for their TPA
  cluster or they are fine with a shared barman instance. The latter is the default but some clients
  might be willing to pay more for an exclusive barman instance as well. Along with this, customers
  might have specific backup schedules which can be accomodated. Again, helpful and appropriate
  defaults will be recommended from our end for this.

### AWS Credentials
===================

  Typically, we will do the deployment on behalf of the customer. The customer can also provide us
  AWS credentials which can then be used to deploy via their user accounts (this needs to be tried out
  appropriately).
  
### SSH Credentials
===================

  The customers can provide us with SSH public keys. These keys can be added to the authorized_keys
  on each of the instances and this ways, the customer can get access to the instances via SSH post
  the deployment. If they do not provide us these keys, then we can generate keys and share with them
  as well
  
### Customer client credentials
===============================

  The customer can also provide a specific IP address from their side which will be used to access the
  database after deployment. If this IP address is provided, then only this will be configured to get
  external access to the PostgreSQL deployment using md5.
  
TPA Provisioning Process Output
===============================

Based on the above inputs from customers (aided by helpful defaults from our side), we will go ahead
and provision the cluster. On successful provisioning (and basic sanity testing) from our side, we
need to share the following details back with the Customer:

###  Inventory of the provisioned instances
===========================================
  The IP addresses of all the instances provisioned as part of the deployment needs to shared as an
  inventory with the customer. The inventory will contain helpful annotations to indicate which IP is
  for the primary, which is for the standby instances and barman instance, etc.
  
### Access credentials for the PostgreSQL user
==============================================

  We should generate a random password for the postgres user and configure the database appropriately
  to allow access to a specific customer client address (if provided). Otherwise, we can configure a
  "0.0.0.0/0 with md5" in pg_hba.conf as well. This random password will be shared with the customer
  
### SSH access credentials
============================ 

  The customer can provide their SSH public key which will be configured on all the instances, otherwise
  we can generate and share relevant credentials.
  
### TPA stack component details
=================================

  We can also shared the TPA version number along with the details of the EXACT version numbers of all
  the different components that got deployed.
