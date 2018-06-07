# coding=utf-8
'''
#---------------------------------------------------------------------------------------------
#  Licensed Materials - Property of IBM
#  5725-M86
#  Copyright IBM Corp. 2017 All Rights Reserved.
#  US Government Users Restricted Rights - Use, duplication or
#  disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
#---------------------------------------------------------------------------------------------
# This module implements version checking. It contains the master
# version number from the associated StoredIQ release.
# The version number is changed manually when the API changes.
'''

CONNECTOR_SDK_VERSION = '1.0.1'

def sdk_product_version():
    return CONNECTOR_SDK_VERSION
