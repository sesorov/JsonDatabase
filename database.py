# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Main component of JsonDatabase
"""

import logging
import os
import pathlib
import sys

from table import JsonManager, Table


class JsonDatabase(Table):

    def __init__(self, file_manager: JsonManager):
        self.file_manager = file_manager
        self._tables = {}

    def table(self, name, primary_keys=None):
        """
        Get table or create one
        :return:
        """

        if name in list(self._tables.keys()):
            return self._tables[name]

        table = Table(name, self.file_manager, primary_keys)
        self._tables[name] = table
        return table

    def drop(self, name):
        """
        Drop table by name (if name == all, drop all)
        :param name:
        :return:
        """

        if name in self._tables:
            del self._tables[name]

        elif name == 'all':
            self.file_manager.write({})
            self._tables = {}
