# -*- coding: utf-8 -*-
#
# Copyright (c) nexB Inc. and others. All rights reserved.
# ScanCode is a trademark of nexB Inc.
# SPDX-License-Identifier: Apache-2.0
# See http://www.apache.org/licenses/LICENSE-2.0 for the license text.
# See https://github.com/nexB/scancode-plugins for support or download.
# See https://aboutcode.org for more information about nexB OSS projects.
#

import os
import sys
from functools import partial
from io import BytesIO
from itertools import chain
from struct import unpack

import attr
from commoncode.cliutils import PluggableCommandLineOption as CommandLineOption
from commoncode.cliutils import SCAN_GROUP
from commoncode import fileutils
from plugincode.scan import ScanPlugin
from plugincode.scan import scan_impl
from typecode import contenttype

from compiledcode.javaclass import javaclass


@scan_impl
class JavaClassScanner(ScanPlugin):
    """
    Scan java class information from the resource.
    """
    resource_attributes = dict(
        javaclass=attr.ib(default=attr.Factory(dict), repr=False),
    )

    options = [
        CommandLineOption(('--javaclass',),
            is_flag=True, default=False,
            help='Collect java class metadata',
            help_group=SCAN_GROUP,
            sort_order=100),
    ]

    def is_enabled(self, javaclass, **kwargs):
        return javaclass

    def get_scanner(self, **kwargs):
        return scan_javaclass


def scan_javaclass(location, **kwargs):
    """
    Return a mapping content  of a class fie
    """
    T = contenttype.get_type(location)
    if not T.is_java_class:
        return

    javaclass_data = dict()
    SHOW_CONSTS = 1
    with open(location, 'rb') as data:
        f = BytesIO(data.read())
    c = javaclass.Class(f)

    javaclass_data['Version'] = 'Version: %i.%i (%s)' % (
        c.version[1], c.version[0], javaclass.getJavacVersion(c.version))

    if SHOW_CONSTS:
        javaclass_data['Constants Pool'] = str(len(c.constants))
        constants = dict()
        for i in range(1, len(c.constants)):
            const = c.constants[i]

            # part of #711
            # this may happen because of "self.constants.append(None)" in Class.__init__:
            # double and long constants take 2 slots, we must skip the 'None' one
            if not const: continue

            constant_data = dict()
            if const[0] == javaclass.CONSTANT_Fieldref:
                constant_data['Field'] = str(c.constants[const[1]][1])

            elif const[0] == javaclass.CONSTANT_Methodref:
                constant_data['Method'] = str(c.constants[const[1]][1])

            elif const[0] == javaclass.CONSTANT_InterfaceMethodref:
                constant_data['InterfaceMethod'] = str(c.constants[const[1]][1])

            elif const[0] == javaclass.CONSTANT_String:
                constant_data['String'] = str(const[1])

            elif const[0] == javaclass.CONSTANT_Float:
                constant_data['Float'] = str(const[1])

            elif const[0] == javaclass.CONSTANT_Integer:
                constant_data['Integer'] = str(const[1])

            elif const[0] == javaclass.CONSTANT_Double:
                constant_data['Double'] = str(const[1])

            elif const[0] == javaclass.CONSTANT_Long:
                constant_data['Long'] = str(const[1])

            # elif const[0] == CONSTANT_NameAndType:
            #   print 'NameAndType\t\t FIXME!!!'

            elif const[0] == javaclass.CONSTANT_Utf8:
                constant_data['Utf8'] = str(const[1])

            elif const[0] == javaclass.CONSTANT_Class:
                constant_data['Class'] = str(c.constants[const[1]][1])

            elif const[0] == javaclass.CONSTANT_NameAndType:
                constant_data['NameAndType'] = str(const[1]) + ', ' + str(const[2])
            else:
                constant_data['Unknown(' + str(const[0]) + ')'] = str(const[1])

            constants[i] = constant_data

        javaclass_data['Constants'] = constants

    access = []
    if c.access & javaclass.ACC_INTERFACE:
        access.append('Interface ')
    if c.access & javaclass.ACC_SUPER_OR_SYNCHRONIZED:
        access.append('Superclass ')
    if c.access & javaclass.ACC_FINAL:
        access.append('Final ')
    if c.access & javaclass.ACC_PUBLIC:
        access.append('Public ')
    if c.access & javaclass.ACC_ABSTRACT:
        access.append('Abstract ')
    if access:
        javaclass_data['Access'] = ', '.join(access)

    methods = []
    for meth in c.methods:
        methods.append(str(meth))
    if methods:
        javaclass_data['Methods'] = methods

    javaclass_data['Class'] = c.name

    javaclass_data['Super Class'] = c.superClass

    interfaces = []
    for inter in c.interfaces:
        interfaces.append(str(inter))
    if interfaces:
        javaclass_data['Interfaces'] = interfaces

    return dict(
        javaclass=javaclass_data,
    )
