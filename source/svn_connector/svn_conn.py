'''
#------------------------------------------------------------------------------------------
# DISCLAIMER OF WARRANTIES.
#   The following code is sample code created by IBM Corporation. IBM grants you a
#   nonexclusive copyright license to use this sample code example to generate similar
#   function tailored to your own specific needs. This sample code is not part of any
#   standard IBM product and is provided to you solely for the purpose of assisting you
#   in the development of your applications. This example has not been thoroughly tested
#   under all conditions. IBM, therefore cannot guarantee nor may you imply reliability,
#   serviceability, or function of these programs. The code is provided "AS IS", without
#   warranty of any kind. IBM shall not be liable for any damages arising out of your or
#   any other parties use of the sample code, even if IBM has been advised of the possibility
#   of such damages. If you do not agree with these terms, do not use the sample code.
#      Licensed Materials - Property of IBM
#      5725-M86
#      Copyright IBM Corp. 2017 All Rights Reserved.
#      US Government Users Restricted Rights - Use, duplication or disclosure restricted by
#      GSA ADP Schedule Contract with IBM Corp.
#------------------------------------------------------------------------------------------
'''
import os, commands
import traceback
import time
import re
import types
from stat import *

from siq_connector.templateconnection import TemplateConnection, TemplatePropertyNames
from siq_connector.templateexceptions import TemplateException, TemplateDirTooLargeException
from siq_connector.templateexceptions import TemplateOtherException, Template_Err
from siq_connector.templateexceptions import TemplateNotConnectedException
from siq_connector.templateexceptions import TemplateFileNotFoundException
from siq_connector.templateexceptions import TemplateInvalidPathException
from siq_connector.templateexceptions import TemplateConnectionError
from siq_connector.templateexceptions import Template_SSL_Exception
from siq_connector.node import Node

import requests
from requests.exceptions import SSLError, ConnectionError
import logging
import pysvn


'''
A simple file handle class to maintain state data for file reads and writes.
'''
class Handle(object):
    def __init__(self, path, mode, size=0, offset=0, url=None):
        self.path    = path
        self.mode    = mode
        self.size    = size
        self.offset  = offset
        self.url     = url
        self.gen     = None
        self.attrMap = None
        self.writeData        = None  # write data bytearray
        self.writeBufCount    = 0     # write buffer current size
        self.writeInputBufMax = 125   # max number of 1MB buffers before Conns write
        self.response = None
        self.os_handle = None

    def __del__(self):
        '''
        Clean up stale OS handle, if any
        '''
        if self.os_handle:
            os.close(self.os_handle)
            self.os_handle = None

    def getOsHandle(self):
        return self.os_handle

    def setOsHandle(self, handle):
        self.os_handle = handle

class TSvnConnector(TemplateConnection):
    # Enable for local logging. Use appropriate log file path
    _mylogger = logging.getLogger("SvnConnector")
    _mylogger.setLevel(logging.DEBUG)
    _mylogger.addHandler(logging.FileHandler("/deepfs/config/sampleconnector.log"))
    DUPLICATE_CHECK_FIELDS = ['share']

    # ------------------------------------------------------------------------
    def __init__(self, serverName, userName, userPwd, options, serial, mountPoint):
        """
        Initialize the SvnConnector connection.
        """
        self._mylogger.info('SvnConnector.__init__(): servname=%s, uname=%s, pwd=%s, options=%s, serial=%s, mountPoint=%s' % (str(serverName), str(userName), str(userPwd), str(options), str(serial), str(mountPoint)))

        # Determine the maximum size of a page of items to return per call during harvest listdir
        self._listdir_page_size = 500

        #---------------------------------------------------
        # serverName:    <host-IP> Example: Server: '9.30.52.63' or 'localhost'
        # Option String: Supported options: multiple options separated by ';'
        #    <share>: Example: 'share=/mnt/demo-A'
        #    <mount>: Example: 'mount=/tmp/my_mount'
        #        - If mount is absent, value of mountPoint is used.
        #---------------------------------------------------
        self._server_name = serverName
        self._userName = userName
        self._userPwd = userPwd
        self._options = options
        self._serial = serial
        self._initial_dir = None
        self._start_dir = None
        self._end_dir = None
        self._top_level = True
        self._is_connect = True
        self._volume_register = False

        # self._share = options.get('share', None)
        # if not self._share:
        #     # self._mylogger.info("SvnConnector.__init__(): servname=%s, uname=%s, options=%s: 'share' missing in options" % (str(serverName), str(userName), str(options)))
        #     # return
        self._mount_base = options.get('mount', None)
        if not self._mount_base:
            self._mount_base = mountPoint

        if self._mount_base.endswith('/'):
            sep = ''
        else:
            sep = '/'
        self._mp = self._mount_base + sep 

        # self._mylogger.info("SvnConnector.__init__(): _mp=%s" % (str(self._mp)))

        # Default parameters set to not require a valid server certificate.
        # TODO: Certificate verification for NFS mount (NFS over SSH tunnel?)


    # ------------------------------------------------------------------------
    @classmethod
    def get_attribute_def(cls):
        '''
        Return array of custom attributes to be registered with StoredIQ later
        '''
        import tsvn_connector.sample_attributes as attr
        return attr.attributes

    # ------------------------------------------------------------------------
    @classmethod
    def get_fs_name(cls):
        '''
        Provide the name of this connector to StoredIQ File Manager
        '''
        from tsvn_connector.sample_attributes import fs_name
        return fs_name

    # ------------------------------------------------------------------------
    def _fqn(self, path):
        '''
        _fqn: get fully qualified name for the given path
              Object paths passed down from StoredIQ are relative to the data source 'mount'
        '''
        fpath = path
        # self._mylogger.info('1) SvnConnector.__fqn(): path=%s' % str(fpath))
        # self._mylogger.info('2) SvnConnector.__fqn(): self._mp=%s' % str(self._mp))
        if not fpath.startswith('/'):
            fpath = self._mp + path
        return fpath

    # ------------------------------------------------------------------------
    def _get_login(self, realm, user, may_save ):
        '''
        This is get login call back function. 
        '''
        return True, self._userName, self._userPwd, False
    
    def ssl_server_trust_prompt(self, trust_dict ):
        '''
        This is ssl server trust prompt.
        '''
        return True, 1, False

    def connect(self):
        """
        Connect to the server containing the share.
        """
        self._mylogger.info('>>>>>>>>>>Connect<<<<<<<<<')
        self._top_level = True
        # self._mylogger.info('SvnConnector.connect(): serverName: %s, userName: %s'  % (self._server_name, self._userName))
        
        if not self._mp:
            # self._mylogger.info('SvnConnector.connect(): Unknown Mount-point: serverName: %s, share: %s'  % (self._server_name, self._share))
            return False

        # Create mount point path, if doesn't exist
        if not os.path.ismount(self._mp):
            if not os.path.exists(self._mp):
                os.makedirs(self._mp)
        else:
            # self._mylogger.info('SvnConnector.connect(): %s, already mounted' % (self._mp))
            # TODO: Unmount only if mounted. Ignore error for now.
            return True
        
        self._top_level = True 
        mount_point = '/deepfs/{0}/svn'.format(self._server_name)
        if not os.path.exists(mount_point):
            self._mylogger.info('>>>>>>>>>>Connect<<<<<<<<< mount_point: %s'% mount_point)
            os.makedirs(mount_point)
        
        cmd = "/bin/mount --bind {0} {1}".format(mount_point, self._fqn(self._mp))
        self._mylogger.info('>>>>>>>>>>Connect<<<<<<<<< bind: %s'% cmd)
        errorcode, output = commands.getstatusoutput(cmd )
        if errorcode:
            emsg = 'mount %s failed, status=%s, msg=%s' % (self._mp, str(errorcode), output)
            raise TemplateInvalidPathException
            
        return True
    # ------------------------------------------------------------------------

    # ------------------------------------------------------------------------
    def disconnect(self):
        """
        Disconnect from the Connections server.
        """
        self._mylogger.info('SvnConnector.disconnect:')
        if self._mp:
            errorcode, output = commands.getstatusoutput('/bin/umount %s' % self._mp)
            self._mylogger.info('SvnConnector.disconnect(): umount %s, status=%s, output=%s' % ( self._mp, str(errorcode), output))
            self._mp = None

        return True

    # ------------------------------------------------------------------------
    def shutdown(self):
        """
        Does a destroy of the Connections server and cleans up all resources.
        """
        self._mylogger.info('SvnConnector.shutdown:')
        self.disconnect()
        return True

    # ------------------------------------------------------------------------
    def _get_extras(self, path):
        '''
        # Build primary attributes for the node given by path into extras.
        # For Sample_connector, we choose to provide information in the primary attribute
        # in addition to the standard (file system metadata) information.
        # In essence, the value (a dictionary) of 'primary_attributes' contains just one key/value pair.
        # The format of 'primary_attributes' that is added to 'extras' is as shown below:
        # { 'primary_attributes' : { 'SampleConnObjFileType' : <File contents type> }}
        # Note that file contents type is retrieved with the help of 'file' command.
        '''
        # Get content type if not a directory
        extras = {}
        fqn = self._fqn(path)
        if not self.is_dir(fqn):
            errorcode, output = commands.getstatusoutput("/usr/bin/file %s" % fqn)
            ctype = 'Unknown content type'
            if not errorcode:
                # Translate output string to nice looking mime type
                if 'ASCII text' in output:
                    ctype = 'text/plain'
                elif 'ASCII C program text' in output:
                    ctype = 'text/C program'
                elif 'executable for python' in output:
                    ctype = 'text/x-python'
                elif 'XML' in output:
                    ctype = 'text/xml'
                elif 'executable,' in output:
                    ctype = 'binary/executable'
            extras['primary_attributes'] = {'SampleConnObjFileType' : ctype}
        return extras

    # ------------------------------------------------------------------------
    def is_read_only(self, path):
        """
        Checks and returns appropriate read/write permissions on the path.
        """
        #self._mylogger.info('SvnConnector.isReadOnly(): path=%s' % path)
        st = self.lstat(path)
        mode = st[ST_MODE]
        rmask = (mode & (S_IRUSR | S_IRGRP | S_IROTH))
        wmask = (mode & (S_IWUSR | S_IWGRP | S_IWOTH))
        if ((rmask == (S_IRUSR | S_IRGRP | S_IROTH)) and wmask == 0):
            return True
        return False

    def get_unsupported_characters(self):
        return ['\\', ':', '*', '?', '"', '<', '>', '|']

    # ------------------------------------------------------------------------
    def create_checkout(self, path):
        svn_client = pysvn.Client()
        svn_client.callback_get_login = self._get_login
        svn_client.callback_ssl_server_trust_prompt = self.ssl_server_trust_prompt
        mount_point = '/deepfs/{0}/svn'.format(str(self._server_name))
        local_checkout = '{0}/{1}'.format(mount_point, path)
        full_url = 'https://{0}/svn/{1}'.format(self._server_name, path)
        #self._mylogger.info('SvnConnector.checkout_mount(): full_url: %s local_checkout: %s'  % (full_url, local_checkout))
        #self._mylogger.info('SvnConnector.checkout_mount(): CheckOUT Started')
        svn_client.checkout(full_url, local_checkout, recurse=True)
        #self._mylogger.info('SvnConnector.checkout_mount(): CheckOUT Complete')
        
        # Build mount command w/ arguments
        # mount --bind afiz /deepfs/imports/template/svn
        cmd = "/bin/mount --bind {0} {1}".format(mount_point, self._fqn(self._mp))
        errorcode, output = commands.getstatusoutput(cmd )
        self._mylogger.info('SvnConnector.checkout_mount(): cmd=%s, status=%s' % ( cmd, str(errorcode)))
        if errorcode:
            emsg = 'mount %s failed, status=%s, msg=%s' % (self._mp, str(errorcode), output)
            raise TemplateInvalidPathException
    
    def start_checkout(self, path):
        mount_point = '/deepfs/{0}/svn/{1}'.format(self._server_name, path)
        if self._volume_register:
            if not os.path.exists(mount_point):
                os.makedirs(mount_point)

    def list_dir(self,node):
        '''
        Lists the files and directories in the specified directory.
        '''
        self._mylogger.info('SvnConnector.list_dir(): Entered >>>>>>>>>>>>LD')
        path = node.path
        extras = node.extras
        
        if self._is_connect:
            self.create_checkout(path)
            self._is_connect = False

        self._mylogger.info('SvnConnector.list_dir(): path=%s, extras=%s' % (path, str(extras)))
        if self._top_level:
            # We're at top level during traversal. Pick user-specified initial-directory
            self._initial_dir = path
        self._top_level = False

        try:
            # With OS help, retrieve child objects of path 
            self._mylogger.info('1) SvnConnector.list_dir(): path=%s' % (str(self._fqn(path))))
            dir_entries = os.listdir(self._fqn(path))
            self._mylogger.info('2) SvnConnector.list_dir(): dir_entries=%s' % (str(dir_entries)))
        except IOError as e:
            #self._mylogger.info('SvnConnector.list_dir(): Error %s, path=%s, extras=%s' % (str(e), path, str(extras)))
            raise 'SvnConnector.list_dir(): Error "%s" on "%s"' % (e, path)

        self.retlist = []
        # When node is top level directory
        if not dir_entries:
            self._mylogger.info('SvnConnector.list_dir(): node_path=%s' % (str(node.path)))
            return self.list_dir_next(node)

        for item in dir_entries:
            #self._mylogger.info('SvnConnector.list_dir(): path=%s, ini_dir=%s, item=%s' % (path, self._initial_dir, item))
            if path:                    # TODO: optimize by pulling fixed code outside loop
                # Construct item_path (relative to mount point) to be returned to File Manager
                #    and lstat_path to obtain lstat properties using OS call
                item_path = lstat_path = path + '/' + item
                if self._initial_dir:
                    # Don't include initial directory in return elements
                    item_path = item_path.lstrip(self._initial_dir)
                if item_path.startswith('/'):
                    item_path = item_path[1:]
            else:
                lstat_path = item_path = item
            #self._mylogger.info('SvnConnector.list_dir(): item_path=%s, lstat_path=%s' % (item_path, lstat_path))
            new_node = Node(item_path, self._get_extras(lstat_path))
            new_node.set_lstat(self.lstat(lstat_path))
            self.retlist.append(new_node)

        #self._mylogger.info('SvnConnector.list_dir(): path=%s, extras=%s' % (path, str(extras)))
        return self.list_dir_next(node)

    # ------------------------------------------------------------------------
    def list_dir_next(self, node):
        '''
        Retrieve the next 'count' items from the current list_dir.
        '''
        #self._mylogger.info('SvnConnector.list_dir_next(): path=%s, extras=%s' % (node.path, str(node.get_extras())))

        self._listdir_page_size = len(self.retlist) + 1
        return self.retlist

    # ------------------------------------------------------------------------
    def lstat(self, path, extras={}):
        '''
        Get the attributes for the specified file.
        If extras has lstat return it. If top level dires return lstat.
        Otherwise return None
        '''
        self._mylogger.info("SvnConnector.lstat(): path=%s, extras=%s" % (path, str(extras)))
        try:
            return tuple(os.lstat(self._fqn(path)))
        except Exception, e:
            self._mylogger.info("SvnConnector.lstat(): Exception, %s on path=%s" % (e, path))
            raise IOError(e)

    # ------------------------------------------------------------------------
    def lstat_extras(self, path, extras={}):
        '''
        Get the file system and the extra attributes for the specified file.
        '''
        #self._mylogger.info('SvnConnector.lstat_extras(): path=%s, extras=%s' % (path, str(extras)))
        return (self.lstat(path, extras), self.get_node(path, extras))

    # ------------------------------------------------------------------------
    def create_file(self, path, size, attrMap):
        """
        Create a file: If the file cannot be created, IOError is raised.
        Returns Handle if successful.
        TODO: Spec for attr dictionaries

        :param path: fully qualified file name including path
        :type  path: str
        :returns: an OSfile handle object.
        """

        fileHandle = Handle(path, TemplateConnection.FILE_WRITE, url=None)
        #self._mylogger.info('SvnConnector.create_file(): path=%s, size=%s, map=%s' % (path, str(size), str(attrMap)))
        try:
            fileHandle.setOsHandle(os.open(self._fqn(path), os.O_RDWR|os.O_CREAT))
        except Exception, e:
            raise IOError(e)

        return fileHandle

    # ------------------------------------------------------------------------
    def _doesFileExist(self, requestPath):
        '''
        _doesFileExist(): Check if file w/ given path exists
        '''
        #self._mylogger.info("SvnConnector._doesFileExist(): requestPath=%s" % requestPath)
        try:
            self.lstat(requestPath)
            return True
        except Exception, e:
            return False

    # ------------------------------------------------------------------------
    def _truncateFile(self, path):
        '''
        _truncateFile(): Truncate file size w/ given path to zero
        '''
        #self._mylogger.info("SvnConnector._truncateFile(): path=%s" % path)
        try:
           return os.open(self._fqn(path), os.O_RDWR|os.O_TRUNC)
        except Exception, e:
            #self._mylogger.info("SvnConnector._truncateFile(): Exception, %s on path=%s" % (e, path))
            raise IOError(e)

    # ------------------------------------------------------------------------
    def open_file(self, path, mode=TemplateConnection.FILE_READ):
        """
        Open a file:
        If the file cannot be opened, IOError is raised.
        Only support modes, FILE_READ and FILE_WRITE.
        An existing file open for FILE_WRITE will truncate the file.
        If mode is omitted, it defaults to FILE_READ
        If mode is FILE_READ and file does not exist, IOError is raised

        :param path: fully qualified file name including path
        :type  path: str
        :returns: a file handle object.
        """

        fileHandle = Handle(path, mode, url=None)
        #self._mylogger.info('SvnConnector.open_file(): path=%s, mode=%s' % (path, str(mode)))

        if mode==TemplateConnection.FILE_READ:
            if not self._doesFileExist(path):
                raise IOError("SvnConnector.open_file: The file, %s cannot be opened." % (path))
            else:
                try:
                    fileHandle.setOsHandle(os.open(self._fqn(path), os.O_RDONLY))
                    #self._mylogger.info("SvnConnector.open_file: The file, %s opened successfully." % (path))
                except Exception, e:
                    #self._mylogger.info("SvnConnector.open_file: Error %s opening %s." % (e, path))
                    raise IOError(e)
        elif mode==TemplateConnection.FILE_WRITE:
            if not self._doesFileExist(path):
                #self._mylogger.info("SvnConnector.open_file: File '%s' doesn't exist, create it." % (path))
                try:
                    fileHandle.setOsHandle(os.open(self._fqn(path), os.O_RDWR|os.O_CREAT))
                except Exception, e:
                    raise IOError(e)
            else:
                #self._mylogger.info("SvnConnector.open_file: File '%s' exists, truncate it." % (path))
                try:
                    fileHandle.setOsHandle(self._truncateFile(path))
                except Exception, e:
                    raise IOError(e)
        else:
            #self._mylogger.info("SvnConnector.open_file:Open mode %s is not supported." % (mode))
            raise IOError("SvnConnector.open_file:Open mode %s is not supported." % (mode))

        return fileHandle

    # ------------------------------------------------------------------------
    def write_file(self, path, fileHandle, filebuf):
        """
        Write to a file:
        Write the buffer passed in to the file handle that is passed in.
        Return the number of bytes of written.
        """
        #self._mylogger.info("SvnConnector.write_file(): path=%s" % (path))
        
        if not fileHandle or not fileHandle.getOsHandle():
            raise IOError("SvnConnector.write_file: File %s, not open." % (path))
          
        if (fileHandle.mode != TemplateConnection.FILE_WRITE) :
            #self._mylogger.info("SvnConnector.write_file: file: '%s' is in mode: %s, write is not allowed" % (path, fileHandle.mode))
            raise IOError("SvnConnector.write_file: file: '%s' is in mode: %s, write is not allowed" % (path, fileHandle.mode))

        w = count = 0
        if (filebuf != None):
            count = len(filebuf)
        
        try:
            w = os.write(fileHandle.getOsHandle(), filebuf)
        except Exception, e:
            raise IOError("SvnConnector.write_file: Error %s on '%s'." % (e, path))

        # TODO: Should short writes be reported?
        #self._mylogger.info('SvnConnector.write: input buffer count: %s' % (count))
        return w

    # ------------------------------------------------------------------------
    def read_file(self, path, fileHandle, readSize):
        """
        Read from a file:
        Read <readsize> bytes from the file (less if the read hits EOF before obtaining size bytes).  Reads from the current
        position of the file handle or the specified offset.

        If readSize is > 0 this number of bytes will be read, less if it hits EOF.
        If readSize is = 0 then a 0 length buffer will be returned
        If readSize is < 0 the whole file will be read from the offset to the end

        If the readOffset in the fileHandle is at or past the EOF, a 0 length buffer is returned.

        returns a buffer containing the bytes that were read.
        """

        buf         = None
        readfileURL = None

        #self._mylogger.info("SvnConnector.read_file(): path=%s, size=%s" % (path, readSize))
        if not fileHandle.getOsHandle():
            raise IOError("SvnConnector.read_file: File %s, not open." % (path))
        try:
            buf = os.read(fileHandle.getOsHandle(), readSize)
        except Exception, e:
            raise IOError("SvnConnector.read_file: Error %s on '%s'." % (e, path))

        return buf

    # ------------------------------------------------------------------------
    def close_file(self, fileHandle):
        """
        Close a file:
        Closes the file represented by the file handle.  Will return the stat and stat extras if they are available at the
        time of close.  If these are not available, they will be retrieve from the repository as part of finishing write
        operations.  These are used to fill the audit and attribute information.  If the stats are not available, and empty
        dictionary is returned.
        """

        #self._mylogger.info('SvnConnector.close:  done')
        if not fileHandle.getOsHandle():
            raise IOError("SvnConnector.close: file not open.")
        try:
            buf = os.close(fileHandle.getOsHandle())
            fileHandle.setOsHandle(None)
        except Exception, e:
            raise IOError("SvnConnector.close: Error %s." % (e))
        return {}

    # ------------------------------------------------------------------------
    def get_audit_attr_names(self, path):
        '''
        Return a list of attribute names to be included in the audit.  When audit is needed,
        StoredIQ will look for these names in the lstat extras.  If the name is found the
        value will be included in the audit information.  If the value is not found in extras,
        then a blank value will be shown.

        If there are no attributes to audit besides the standard file system attributes,
        this method should return an empty list.

        For now, will add the content address, block size, and storage policy to the audit.
        Can assess whether others are needed.
        '''
        return []

    # ------------------------------------------------------------------------
    def setTimestamps(self, path, mtime, atime):
        '''
        Set the timestamp attributes for the specified file.
        '''
        #self._mylogger.info('SvnConnector.setTimestamps path: >%s< '  % (path))
        try:
            os.utime(self._fqn(path), (mtime, atime))
        except Exception, e:
            raise IOError("SvnConnector.setTimestamps: Error's'" % (e))

        return True

    # ------------------------------------------------------------------------
    def makedirs(self, path):
        '''
        Make directory
        '''

        #self._mylogger.info('SvnConnector.makedirs():  path->%s< ' % (path))
        try:
            os.makedirs(self._fqn(path))
        except Exception, e:
            raise IOError("SvnConnector.makedirs: Error %s." % (e))

        return True

    # ------------------------------------------------------------------------
    def rmdir(self, path):
        '''
        Remove directory
        '''
        #self._mylogger.info('SvnConnector.rmdir():  path->%s< ' % (path))
        try:
            p = path
            if not path.startswith('/'):
                p = self._fqn(path)
            os.rmdir(p)
        except Exception, e:
            raise IOError("SvnConnector.rmdir: Error %s." % (e))
        return True

    # ------------------------------------------------------------------------
    def unlink(self, path):
        '''
        Deletes a file.
        '''
        #self._mylogger.info('SvnConnector.unlink:  path->%s< ' % (path))
        try:
            p = path
            if not path.startswith('/'):
                p = self._fqn(path)
            os.unlink(p)
        except Exception, e:
            #self._mylogger.info("SvnConnector.unlink(): Exception, %s on path=%s" % (e, path))
            raise IOError("SvnConnector.unlink: Error %s." % (e))
        return True

    # ------------------------------------------------------------------------
    def get_list_dir_page_size(self):
        '''
        Returns the page size that will be used when calling list_dir().  Should return a value < 1 if
        there is no paging.  By default this returns 0.
        '''
        return self._listdir_page_size

    # ------------------------------------------------------------------------
    def validate_directories_in_filemgr(self):
        '''
        Validate all three paths
        '''
        return True

    # ------------------------------------------------------------------------

    def validate_directories(self, path, startDir, endDir):
        '''
        Validates that the initial directory, the start directory, and the end directory are
        valid for a volume definition.  If not specified in the configuration, these directories
        may be set to None.  It is up to the file manager implemenation to determine whether
        None values are valid.

        Returns a list of error messages found when checking the directories.  Returns
        None or an empty collection if all of the directories are valid.  If any excpeiton
        is raised by the implementation, it is assumed the directories are not valid.
        '''
        #self._mylogger.info("SvnConnector.validate_directories(): path >%s< startDir: >%s< endDir: >%s<" % (path, startDir, endDir))
        if not self._volume_register:
            self._volume_register = True
            self.start_checkout(path)
            
        errlist = []
        if not self.is_dir(self._fqn(path)):
            errlist.append("path '%s' is not a valid directory." % path)
        else:
            self._initial_dir = path
        
        if startDir and not self.is_dir(self._fqn(path + '/' + startDir)):
            errlist.append("startDir '%s' is not a valid directory." % startDir)
        else:
            self._start_dir = startDir
        
        if endDir and not self.is_dir(self._fqn(path + '/' + endDir)):
            errlist.append("endDir '%s' is not a valid directory." % endDir)
        else:
            self._end_dir = endDir
        #self._mylogger.info("SvnConnector.validate_directories(): idir=%s, sdir=%s, edir=%s" % (self._initial_dir, self._start_dir, self._end_dir))
            
        return errlist

    # ------------------------------------------------------------------------
    def verify_mount_in_filemgr(self):
        '''
        Connections validates mounts to avoid costly calls to list_dir()
        '''
        #self._mylogger.info("SvnConnector.verify_mount_in_filemgr():")
        return True

    # ------------------------------------------------------------------------
    def verify_mount(self, path='', includeDirs=None):
        '''
        This validates that the path exists to determine readability.  It calls
        isReadOnly to determine writability, which is currently not implemented.
        It does not validate the includeDirs as this requires a list_dir, which may
        be inefficient.
        '''
        verified = True
        errlist  = []
        readable = False
        writable = False

        #self._mylogger.info('SvnConnector.verify_mount(): path=%s, includeDirs=%s' % (path, includeDirs))
        try:
            readable = self.is_dir(path)
        except Exception, err:
            #self._mylogger.info("SvnConnector.verify_mount(): %s failed checking path. (%s)" % (path, err))
            errlist.append(str(err))
            verified = False
            
        try:
            writeErrlist, writable, deleted = self._verify_write(path)
            errlist.extend(writeErrlist)           
        except Exception, err:
            #self._mylogger.info("SvnConnector.verify_mount(): %s failed verifying write. (%s)" % (path, err))
            errlist.append(str(err))
            
        return (verified, errlist, readable, writable)

if __name__ == '__main__':
    print 'sample_conn.main(): started'