## ** work in progress **
# Enhance IBM StoredIQ capabilities with new data sources using Connector SDK 

IBM storedIQ platform provides Powerful solutions for managing unstructured data in-place. IBM® Unstructured Data Identification and Management addresses the problems that challenge records management, electronic discovery, compliance, storage optimization, and data migration initiatives. By providing an in-depth assessment of unstructured data where it is, this software gives organizations visibility into data to make more informed business and legal decisions.

All these features of storedIQ can be utilized by making a connection between data source and storedIQ suite. This connection between storedIQ and data source is established using a connector. A Connector is a software component of IBM StoredIQ that is used to connect to a data source such as a SVN server and helps in accessing its data.  Using IBM StoredIQ Connector API SDK developers of other companies can develop Connectors to new data sources outside IBM StoredIQ development environment. These Connectors, then, can be integrated with a live IBM StoredIQ. Once the connection is established between data sources and storedIQ using connector, user can perform all desired operation supported by storedIQ on data sources.

The main approach used in developing connector is to find a way to checkout all the content of desired data source into the local server of storedIQ. Once all the files are checked out in local server, user can run a harvest to see all the content of data source in storedIQ suite.

This code pattern gives you step by step instructions for developing a connector to connect SVN server and IBM storedIQ. When the user has completed this code pattern, they will understand how to develop, integrate, register and test the connector.

## Flow

## Included Components

## Featured Technologies

## Watch the Video

TBD

## Pre-requisites

* IBM StoredIQ Product – refer link to install the product on server
*	IBM StoredIQ Connector API SDK – refer doc to setup the SDK
*	Python version 2.6
* SVN Server - 

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
