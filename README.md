### About script
This script is created for making snapshots of EC2 volumes. It handles creating and deleting old snapshots which passed its retention time.
### Requirements
* Python3
* AWS CLI installed (https://aws.amazon.com/cli/)
### Script installation
1. Install AWS CLI and configure it using ```aws configure``` command
2. Install needed dependencies:
```pip3 install -r requirements.txt```
3. Set variables inside script to fit your needs
4. Run script manually or add it to cron

***Remember that you'll need AWS credentials to be configured on each user willing to run script (because of its location inside user's home directory).***

_or alternatively set them inside /etc/boto.cfg to grant access globally_
