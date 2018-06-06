## ** work in progress **
# Enhance IBM StoredIQ capabilities with new data sources using Connector SDK 

Data is growing exponentially. We are the creators and consumers of data. With this growth of data, organizations find it difficult to manage this effectively. This growth in data has also contributed to new challenges like security, governing and protecting privacy. IBM StoredIQ platform provides powerful solutions for managing unstructured data in-place. It addresses the problems of records management, electronic discovery, compliance, storage optimization, and data migration initiatives. 

Organizations have freedom to choose data sources for their need. It may involve multiple data sources with different versions. A data source can be considered as a location which contains unstructured content. By providing an in-depth assessment of unstructured data where it is, the StoredIQ gives organizations visibility into data to make more informed business and legal decisions. Data Source is an important part for IBM Stored IQ solution. Stored IQ provides flexibility to customers to choose data source and it supports 85+ data sources out of the box. Some of the data sources include Box, Microsoft Office 365, FileNet etc. All the features of IBM StoredIQ can be utilized by making a connection between a data source and StoredIQ. The connection between a data source and StoredIQ is established using a connector.  

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

* **Connection management**
 
  The APIs in this group manage connections to the data source.
  
* **Data object traversal management**

  APIs in this group manage data traversal. By default, StoredIQ traverses data source tree in depth-first pattern.
  
* **Attribute management**

  APIs in this group manage custom attributes. The standard attributes of a data object collected by Stored IQ by default includes size, access times etc.
  
* **Content access management**

  APIs in this group manage the content that is retrieved from the data objects like open file, read file and so on.

To develop a connector, need to implement these APIs.

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

Now `svn_connector` contains following python modules:

* **`__init__.py`**

  It is as per the python convention to treat the directory as containing package.
  
* **sdk_version.py**

  Avoid making changes to this. This module is provided for version compatibility enforcement.
  
* **sample_attributes.py**

  Change the name of the data source in sample_attributes.py. Here we are giving data source name as `svn-template`.
  
  ![image1](images/img1.png)

  > Note: fs_name could be anything.
  
* **sample_conn.py**

  Rename this file as `svn_conn.py`. The actual code for svn data source connector is written in the `svn_conn.py` module. The
  svn_conn.py will be containing APIs to connect and traverse through data sources. As mentioned in [Methodology](#methodology), need to add code for all four categories. 
  
  High level code for svn connector can be explained as follows.
  
  * *connect()* uses the information provided by constructor method to establish connection with the server that hosts the data source. The constructor method provides information that is collected by using the `Add Volume UI` dialog (explained in Test section).
  
  * *Create mount point*. It checks if the path for mount point exists, else it creates the path and bind that path for a local checkout.
  
  * *validate_directories()* creates new initial directory with the same name as of svn repository/directory which we want to checkout. This name will be given by user from storedIQ interface. [Need to confirm??]
  
  * *checkout* all the files from a specific repository of svn server to <local server??>. To achieve this for svn data source, `pysvn.Client.checkout()` is used from pysvn package. After checkout, mount all these files to the mount point created earlier.
  
  * *list_dir()* lists the files and sub-directories in the specified repository. This method gets called when we harvest the newly added volume in StoredIQ. The firt time call of list_dir(), internally calls checkout function.
  
  * *lstat()* gets called if a directory is chosen to list the files. This method retrieves the file system-specific attributes like size for the specified file.
  
  > Note: This pattern provides you code only for read capability of svn connector. 

### 2. Integrate the connector with live IBM StoredIQ

To integrate the connector with live Stored IQ, need to copy the directory that contains the Connector code i.e. `svn_connector` directory in each Data Server and Gateway. The command to execute on your development system will be :

```
 # for Data server
 scp –rp svn_connector root@<IP address of Dataserver>:/usr/lib/python2.6/site-packages
 
 # for Gateway
 scp –rp svn_connector root@<IP address of Gateway>:/usr/lib/python2.6/site-packages
```
> If development system is windows, then copy operation can be done using winscp.

### 3. Register the Connector with live IBM StoredIQ

To register the connector, perform the following steps on each Data Server and Gateway.

1.	Change your directory to site-packages.
   
   ```
   cd /usr/lib/python2.6/site-packages
   ```
  
2. Run the following command.

   python32 /usr/loca/storediq/bin/register_connector.py -c <classpath> [-w ’yes’ | ’no’]
 
   For example, if your Connector folder is my_connector, class name is MyConnector and the module that defines the class is my_module, then class-path is'my_connector.my_module.MyConnector' (quotes included).
   
   For the -w option, if it is specified, it indicates that the Connector is a read-write Connector.
   
   ```
   python32 /usr/local/storediq/bin/register_connector.py -c svn_connector.svn_conn.SvnConnector
   ```

   > Run the command python32 /usr/loca/storediq/bin/register_connector.py -h for more information.
   
3. Restart services on the Data Server and Gateway. Use the following command to restart.
  
   ```
   service deepfiler restart
   ```

### 4. Test the Connector by adding new volume for svn connector

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
