# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Main component of JsonDatabase
"""

import logging
import os
import pathlib
import sys

from table import JsonManager, Table, Document


class JsonDatabase(Table):

    def __init__(self, file_manager: JsonManager):
        self.file_manager = file_manager
        self._tables = self._get_tables()

    def _get_tables(self):
        """
        Get tables instances
        :return:
        """

        content = self.file_manager.read()
        if not content:
            return {}
        tables_names = list(content.keys())
        if '__params__' in tables_names:
            tables_names.remove('__params__')

        params = content['__params__']
        return {name: Table(name, self.file_manager, params[name]['keys']) for name in tables_names}

    def table(self, name, primary_keys=None):
        """
        Get table or create one
        :return:
        """

        if name in list(self._tables.keys()):
            return self._tables[name]

        table = Table(name, self.file_manager, primary_keys)
        if name != '__params__':
            self.table('__params__').add(Document({"keys": primary_keys or []}, name))
        self._tables[name] = table
        return table

    def drop_table(self, name):
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

    def get_tables_names(self):
        return list(self._tables.keys())

    @staticmethod
    def drop(path: str):
        """
        Drop database by name/path
        :param path:
        :return:
        """

        remove_db = pathlib.Path(path)
        remove_db.unlink(missing_ok=True)
