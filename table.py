# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
JsonDatabase base class (table)
"""

import os
import json

from pathlib import Path


class Document(dict):
    """
    A document stored in the database.
    """

    def __init__(self, value, doc_id: int):
        super().__init__(value)
        self.doc_id = doc_id

class JsonManager:
    """
    JSON file operations manager
    """

    def __init__(self, path: Path, encoding='utf-8'):
        """
        Create instance for JSON file manager
        """

        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.is_file():
            with path.open('w', encoding=encoding):
                pass
        self.encoding = encoding
        self.file = path

    def read(self):
        """
        Read JSON file
        :return:
        """

        with self.file.open('r', encoding=self.encoding) as handle:
            return json.load(handle)


class Table:
    """
    Table stored in database (like collection in mongo)
    """

    def __init__(self, name: str, file_manager: JsonManager):
        """
        Create instance for database from provided JsonManager
        """
        self._name = name
        self.file_manager = file_manager
        self._next = None

    @property
    def name(self) -> str:
        """
        Get current table name
        :return: str
        """
        return self._name

    def __len__(self):
        """
        Get size of current table
        :return:
        """

        try:
            table = self.file_manager.read()[self.name]
            return len(table)
        except KeyError:
            return 0

    def __str__(self) -> str:
        """
        Get main info about table as str
        :return: str
        """

        return f"NAME: {self.name}\nSIZE: {len(self)}"

    def __iter__(self):
        """
        Iterate over data in current table
        :return:
        """

        for _id, record in self.read().items():
            yield _id, record

    def read(self):
        """
        Read data in current table
        :return:
        """

        try:
            table = self.file_manager.read()[self.name]
            return {_id: record for _id, record in table.items()}
        except KeyError:
            return {}
