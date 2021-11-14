# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
JsonDatabase base class (table)
"""

import os
import json
import inspect

from pathlib import Path

from query import Query


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

        try:
            with self.file.open('r', encoding=self.encoding) as handle:
                return json.load(handle)
        except json.decoder.JSONDecodeError:
            return {}

    def write(self, data):
        """
        Write dict to .json
        :param data:
        :return:
        """

        with self.file.open('w', encoding=self.encoding) as handle:
            json.dump(data, handle, indent=4)


class Table:
    """
    Table stored in database (like collection in mongo)
    """

    def __init__(self, name: str, file_manager: JsonManager, keys: list = []):
        """
        Create instance for database from provided JsonManager
        """
        self._name = name
        self.file_manager = file_manager
        self.keys = keys
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
        except (KeyError, json.decoder.JSONDecodeError):
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
            yield Document(record, _id)

    def get_next_id(self):
        """
        Get id for the new added document
        :return:
        """

        if self._next:
            next_id = self._next
            self._next += 1
            return next_id

        table = self.read()
        if not table:
            next_id = 1
            self._next = next_id + 1
            return next_id

        last_id = int(max(list(table.keys())))
        next_id = last_id + 1
        return next_id

    def read(self):
        """
        Read data in current table
        :return:
        """

        try:
            table = self.file_manager.read()[self.name]
            return {_id: record for _id, record in table.items()}
        except (KeyError, json.decoder.JSONDecodeError):
            return {}

    def add(self, document):
        """
        Add a new document to table
        :param document:
        :return:
        """

        if isinstance(document, Document):
            _id = document.doc_id

            # We also reset the stored next ID so the next insert won't
            # re-use document IDs by accident when storing an old value
            self._next = None
        else:
            _id = self.get_next_id()

        def updater(table):
            document_key = {key: document[key] for key in self.keys}
            primary_key_exists = any([set(document_key.items()).issubset(set(record.items()))
                                      for record in table.values()]) if document_key else False
            assert _id not in table and not primary_key_exists, f"[ADD][ERROR]: Record already exists."
            table[_id] = document

        try:
            self.update_table(updater)
        except AssertionError as err:
            print(err)

        return _id

    def delete(self, query=None, ids=None):
        """
        Remove documents (matching params) from table
        :param query:
        :param ids:
        :return:
        """

        if ids:
            def updater(table):
                for _id in ids:
                    table.pop(_id)

            self.update_table(updater)
            return ids

        deleted = []

        if query:
            def updater(table):
                for _id in list(table.keys()):
                    if query(table[_id]):
                        table.pop(_id)
                        deleted.append(_id)
            self.update_table(updater)

        return deleted

    def update_table(self, updater):
        """
        Update table data based on updater function
        :param updater: helper-function for updating
        :return:
        """

        tables = self.file_manager.read()

        try:
            raw_table = tables[self.name]
        except (KeyError, json.decoder.JSONDecodeError):
            raw_table = {}

        table = {_id: record for _id, record in raw_table.items()}
        updater(table)

        tables[self.name] = {_id: record for _id, record in table.items()}
        self.file_manager.write(tables)

    def get_all(self):
        """
        Get all data from table
        :return:
        """

        return list(iter(self))

    def search(self, query):
        """
        Search through all records in table (like WHERE in SQL)
        :return:
        """
        # print("table.search.query type: ", type(query))
        # print("table.search.query._test: ", inspect.getsource(query._test))

        return [record for record in self if query(record)]

    def reset(self):
        """
        Delete all data in table
        :return:
        """

        self.update_table(lambda table: table.clear())
        self._next = None
