## ** work in progress **
# Enhance IBM StoredIQ capabilities with new data sources using Connector SDK 

IBM StoredIQ platform provides powerful solutions for managing unstructured data in-place. Unstructured Data Identification and Management addresses the problems that challenge records management, electronic discovery, compliance, storage optimization, and data migration initiatives. By providing an in-depth assessment of unstructured data where it is, the StoredIQ gives organizations visibility into data to make more informed business and legal decisions.

All these features of IBM StoredIQ can be utilized by making a connection between a data source and StoredIQ suite. This connection between a data source and StoredIQ is established using a connector. A Connector is a software component of IBM StoredIQ that is used to connect to a data source such as a SVN server and helps in accessing its data.  Using IBM StoredIQ Connector API SDK any developer can develop Connectors to new data sources outside IBM StoredIQ development environment. These Connectors, then, can be integrated with a live IBM StoredIQ. Once the connection is established between a data source and IBM StoredIQ using connector, user can perform all desired operation supported by StoredIQ on data sources.

The main approach used in developing connector is to find a way to download all the content of desired data source into the IBM  StoredIQ data server. Once all the files are downloaded, an user can harvest (index) to see all the content of data source in StoredIQ suite and information set(infoset) gets created. This infoset can be used to provide insight into an organization’s unstructured content at a given point in time.

This code pattern gives you step by step instructions for developing a connector to connect SVN server data source and IBM storedIQ. When the user has completed this code pattern, they will understand how to develop, integrate, register and test the connector for IBM StoredIQ.

## Flow

## Included Components

* [IBM StoredIQ](https://www.ibm.com/support/knowledgecenter/en/SSSHEC_7.6.0/overview/overview.html)

* [SVN Server](https://docs.oracle.com/middleware/1212/core/MAVEN/config_svn.htm#MAVEN8824): Subversion is a version control system that keeps track of changes made to files and folders or directories, thus facilitating data recovery and providing a history of the changes that have been made over time.

## Featured Technologies

* [Python](https://www.python.org/): Python is a programming language that lets you work quickly and integrate systems more effectively.

## Watch the Video

TBD

## Pre-requisites

* [IBM StoredIQ](https://www.ibm.com/support/knowledgecenter/en/SSSHEC_7.6.0/overview/overview.html) Product: Refer this [link](https://www.ibm.com/support/knowledgecenter/en/SSSHEC_7.6.0/deploy/cpt/cpt_installation_siqplatform.html) to install IBM StoredIQ.
*	IBM StoredIQ Connector API SDK: After the product installation, you will find Connector API SDK at `/usr/lib/python2.6/site-packages/` in StoredIQ Data server ????.
*	[Python version 2.6](https://www.python.org/download/releases/2.6/)
* [SVN Server](https://docs.oracle.com/middleware/1212/core/MAVEN/config_svn.htm#MAVEN8824): Setup SVN server.

## Steps

### 1. Develop the IBM StoredIQ Connector by using Connector API SDK

Once the user have installed StoredIQ Connector, the user will have a folders named as sample_connector and siq_connector. The siq_connector contains python modules that will act as a template for developing a new connector.
Sample_connector contains an implementation of connector for NFSv3 file system. To make the development of connector simpler, we will modify this folder contents in this code pattern. We will rename the folder name relevant to new connector name. In our case we will rename it to tsvn_connector. This folder will be containing following python modules:
* __init__.py
* sample_attributes.py
* sample_conn.py
* sdk_version.py
Avoid making any changes to __init__.py and sdk_version.py. 

## License
[Apache 2.0](LICENSE)
