## ** work in progress **
# Enhance IBM StoredIQ capabilities with new data sources using Connector SDK 

Data is growing exponentially. We are the creators and consumers of data. With this growth of data, organizations find it difficult to manage this effectively. This growth in data has also contributed to new challenges like security, governing and protecting privacy. IBM StoredIQ platform provides powerful solutions for managing unstructured data in-place. It addresses the problems of records management, electronic discovery, compliance, storage optimization, and data migration initiatives. 

Organizations have freedom to choose data sources for their need. It may involve multiple data sources with different versions. A data source can be considered as a location which contains unstructured content. By providing an in-depth assessment of unstructured data where it is, the StoredIQ gives organizations visibility into data to make more informed business and legal decisions. Data Source is an important part for IBM Stored IQ solution. All the features of IBM StoredIQ can be utilized by making a connection between a data source and StoredIQ. The connection between a data source and StoredIQ is established using a connector. Stored IQ provides flexibility to customers to choose data source and it supports 85+ data sources out of the box. Some of the data sources include Box, Microsoft Office 365, FileNet etc. 

The recent release of IBM StoredIQ added a Connector API SDK which can be used by business partners and customers to create custom connector for new data sources which StoredIQ does not support. The IBM StoredIQ Connecter API SDK simplifies connector development by decoupling connector logic from the StoredIQ application logic. It can also be used to customise and extend existing connector. Once you create a new connector, you can use it to manage data in Stored IQ just like you do it with the supported data sources.

This code pattern helps you to understand the methodology and the steps of building a connector of a new data source. In this pattern, we explain the steps for developing a connector for SVN server data source. When the user has completed this code pattern, they will understand how to develop, integrate, register and test the connector for IBM StoredIQ.

## Flow

## Included Components

* [IBM StoredIQ](https://www.ibm.com/support/knowledgecenter/en/SSSHEC_7.6.0/overview/overview.html)

* [SVN Server](https://docs.oracle.com/middleware/1212/core/MAVEN/config_svn.htm#MAVEN8824): Subversion is a version control system that keeps track of changes made to files and folders or directories, thus facilitating data recovery and providing a history of the changes that have been made over time.

## Featured Technologies

* [Python](https://www.python.org/): Python is a programming language that lets you work quickly and integrate systems more effectively.

## Watch the Video

TBD

## Methodology

All operations that are run by IBM StoredIQ application on data objects are categorized as the following APIs:

* Connection management
* Data object traversal management
* Attribute management
* Content access management

To develop a connector, need to implement these APIs.
The main approach used in developing connector is to find a way to download all the content of desired data source into the IBM  StoredIQ data server. Once all the files are downloaded, an user can harvest (index) to see all the content of data source in StoredIQ suite and information set(infoset) gets created. This infoset can be used to provide insight into an organization’s unstructured content at a given point in time.

## Pre-requisites

* [SVN Server](https://docs.oracle.com/middleware/1212/core/MAVEN/config_svn.htm#MAVEN8824): Setup SVN server.

## Steps

### 1. Develop the IBM StoredIQ Connector 

Connector API SDK shares the Python modules with the user that acts as a template for developing a new connector. These modules contain the default implementation and the utility functions. These shared modules come preinstalled in the `/usr/lib/python2.6/site-packages/siq_connector` folder. More details for these modules can be found [here](pdf path??).

The connector API SDK also includes code that implements a fully working NFS based sample connector. This sample connector is also preinstalled at `/usr/lib/python2.6/site-packages/sample_connector` folder. To make development of a new data source connector simpler, we have chosen this `sample_connector` as a base code. We will copy this folder as a new connector folder. In this pattern, we have given name as `svn_connector`.

```
$ cd /usr/lib/python2.6/site-packages
$ cp -r sample_connector svn_connector
```

Now svn_connector contains following python modules:
* `__init__.py`: It is as per the python convention to treat the directory as containing package.
* `sdk_version.py`: Avoid making changes to this. This module is provided for version compatibility enforcement.
* sample_attributes.py
* sample_conn.py
* sdk_version.py

Change the name of the data source in sample_attributes.py. Here we are giving data source name as ‘tsvn-template’(any name).

Note: fs_name could be anything.
Our actual code for svn connector will go into sample_conn.py module. The sample_conn.py will be containing APIs to connect and traverse through data sources. We will make changes to following API:

Connect() – It uses the information provided by constructor method to establish connection with the server that hosts the data source.

Create mount point. check if the path for mount point exists, if not then we will create a path and bind that path for a local checkout.

validate_directories() – 
Create new initial directory with the same name as of svn repository/directory which we want to checkout. This name will be given by user from storedIQ interface.For this purpose we have added a function named <..>.

list_dir() – This method lists the files and sub-directories in the specified repository/directory. 
To do this, we will start checking out all the file from svn server to local server. To achieve the same, we have added a function called create_checkout(). This method will be called when we will harvest the newly added volume in storedIQ.
For svn data source, pysvn package has been used. To do that we will make a connection to svn server and then we will checkout files using pysvn.Client.checkout(). Once checkout is complete, we will mount all these files to mount point created earlier. 

There are some more APIs in template available sample_connector.py which will be called from storedIQ interface but we are not modifying.

lstat() - This method retrieves the file system-specific attributes for the specified file.

list_dir_next() - This method retrieves the next itemCount items from the list of items that is provided by most recent list_dir() call.

lstat_extras() – This method is used to get the file system and the extra attributes for the specified file.

get_list_dir_page_size() - Returns the page size that is used in calls to list_dir().

### 2. Integrate the IBM StoredIQ Connector with live IBM StoredIQ application

This step involves the simple copy action. Copy the tsvn_connector folder that contains the Connector code to each Data Server (DS) and Gateway (GW). For example, the command to execute on your development system can be 
scp –rp <my_connector> root@ <IP address of Dataserver>/usr/lib/python2.6/site-packages
we will use the same command to copy tsvn_connector to gateway server.
For windows this can be done using winscp.

### 3. Register the svn Connector with the live IBM StoredIQ application

On each data server and gateway do the following steps:
a)	cd to site-packages.
b)	Run the command 
python32 /usr/loca/storediq/bin/ register_connector.py -c <classpath> [-w ’yes’ | ’no’].  
For example, if your Connector folder is my_connector, class name is MyConnector and the module that defines the class is my_module, then class-path is'my_connector.my_module.MyConnector' (quotes included).
For the -w option, if it is specified, it indicates that the Connector is a read-write Connector. 
In our case it would be:
python32 /usr/local/storediq/bin/register_connector.py -c tsvn_connector.tsvn_conn.TSvnConnector

Run the command python32 /usr/loca/storediq/bin/ register_connector.py -h for more information.
c)	Restart services on the data server and gateway by using this command: 
service deepfiler restart

(    Need to put steps screenshots in mac here  )

### 4. Test the newly added svn connector by adding new volume for svn connector

* Once the connector is successfully integrated with storedIQ, it will be visible in UI of storedIQ as a new source type.
* Now we can select our connector as source type and fill other details in UI as follows:

  Server name – It is domain name or IP address of svn server.
  
  Username – It is required to authenticate user to remote svn server.
  
  Password – It is password of svn server required to authenticate user to remote svn server.
  
  Volume name – This will be the name of our newly added volume. It could be any name.
  
  Initial Directory – It will be name of any directory from where we will start checkout.
  
  Class name – This will be the class path name as discussed earlier.
 
* Once the volume is added successfully, it will be available in list of volume in UI.

* Now harvest can be run on newly added volume to see the content of svn server in storedIQ UI. To do that select the newly added volume from the list of volumes and click on the harvest. Further it will ask for harvest name which could be anything and will give few options to select such as immediate or schedule harvest and full or incremental harvest.

* Once the harvest is complete, the details of newly added volume in UI will get updated and will show number of data objects added and total

* Create Infoset to see the content of svn server in storedIQ interface and to read the content of files . To do that go to system infosets create new infoset. Give the details required and select newly added volumes from available volumes and click add and finally save.

* After creating the infoset go to data workbench from the storedIQ interface.

* Data workbench will show list of infoset status and state. Select the infoset added in previous step from the list.

* Once infoset is selected, all the contents of your svn server would be visible and content of file can be seen by clicking file name. 







## License
[Apache 2.0](LICENSE)
