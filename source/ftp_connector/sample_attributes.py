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
from siq_connector.attributedefs import AttributeDef, AttributeType, AttributeValueType


# TODO: Define attributes


# Name of the data-source (file system) that this Connector connects to.
fs_name = 'ftp-template'


# Custom Attributes used in SampleConnector
# - It is a dictionary that can contain multiple attributes
# - Each attribute is of the form 'key' : 'value'
# - 'key' string is the name of the attribute. For SampleConnector class,
#       we have single attribute, which describes the type of file contents.
#       SampleConnector._get_attributes() method determines the type file contents
#       using 'file' command and stores in mime-type.
#   value is of type AttributeDef class defined in siq_connector/attributedefs.py
#       Notice that 'key' of the attribute definition is 'SampleConnObjFileType',
#       which same as 'AttributeDef.name' property. That's how it should be for now.
# - Note that Attribute.at_type property is initialized to AttributeType.dense_single.
#       TODO: Describe various properties of Attribute class.
#       Use 'sparse_single' as we don't expect to find content type for all data objects.
#
attributes = {
    'SampleConnObjFileType': AttributeDef(
        'SampleConnObjFileType', 'Type of sample Connector object type',
        AttributeType.sparse_single, AttributeValueType.string, fs_name
    ),
}
