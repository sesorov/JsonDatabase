"""
SQL-like queries class
"""
import re
import sys
import inspect


def where(key: str):
    return Query()[key]


def hashable(obj):
    """
    Make object immutable and thus hashable.
    """
    if isinstance(obj, dict):
        # Transform dicts into ``FrozenDict``s
        return FrozenDict((k, hashable(v)) for k, v in obj.items())
    elif isinstance(obj, list):
        # Transform lists into tuples
        return tuple(hashable(el) for el in obj)
    elif isinstance(obj, set):
        # Transform sets into ``frozenset``s
        return frozenset(obj)
    else:
        # Don't handle all other objects
        return obj


class FrozenDict(dict):

    def __init__(self, *args, **kwargs):
        super().__init__()
        self._d = dict(*args, **kwargs)
        self._hash = None

    def __iter__(self):
        return iter(self._d)

    def __len__(self):
        return len(self._d)

    def __getitem__(self, key):
        return self._d[key]

    def __hash__(self):
        # hash(tuple(sorted(self._d.iteritems()))) -> 0(n)
        if self._hash is None:
            hash_ = 0
            for pair in self.items():
                hash_ ^= hash(pair)
            self._hash = hash_
        return self._hash


class Instance:
    """
    Query instance, multiple can be combined using logical operators
    """

    def __init__(self, test, hash_value):
        self._test = test
        self._hash = hash_value

    def __call__(self, value):
        """
        Check if query matches given value
        :param value:
        :return:
        """
        #print("Calling query instance with value: ", value)

        return self._test(value)

    def __hash__(self):
        return hash(self._hash)

    def __eq__(self, other):
        if isinstance(other, Instance):
            return self._hash == other.hash
        return False

    def __and__(self, other):
        return Instance(lambda value: self(value) and other(value),
                        ('and', frozenset([self._hash, other.hash])))

    def __or__(self, other):
        return Instance(lambda value: self(value) or other(value),
                        ('or', frozenset([self._hash, other.hash])))

    def __invert__(self):
        return Instance(lambda value: not self(value),
                        ('not', self._hash))

    @property
    def hash(self):
        return self._hash


class Query(Instance):
    """
    Query operating tool class
    Usage:
    1. database.search(where('somekey') == 'someval')
    2. database.search(parent.field == 'someval')
    """

    def __init__(self):
        self._field_path = ()

        def notest(_):
            raise RuntimeError('Empty query was evaluated')

        super().__init__(test=notest, hash_value=(None,))

    def __hash__(self):
        return super().__hash__()

    def __getattr__(self, item: str):
        query = type(self)()
        query._field_path = self._field_path + (item,)
        query._hash = ('field_path', query._field_path)

        return query

    def __getitem__(self, item: str):
        return self.__getattr__(item)

    def proc_test(self, test, hash_value):
        """
        Proceed a query from test function.
        :param test:
        :param hash_value:
        :return:
        """

        if not self._field_path:
            raise ValueError('[QUERY][ERROR] No path was set.')

        def runner(value):
            try:
                for part in self._field_path:   # for every criteria (like 'name', 'surname')
                    value = value[part]     # we define value (value[name] = some_name)
            except (KeyError, TypeError):
                return False    # no such criteria
            else:
                #print("Testing ", value)
                #print("Test source: ", inspect.getsource(test))
                return test(value)

        return Instance(lambda value: runner(value), hash_value)

    def __eq__(self, match):
        """
        Test a dict value for equality.
        :param match: User-given value to compare against
        """
        return self.proc_test(
            lambda value: value == match,
            ('==', self._field_path, hashable(match))
        )

    def __ne__(self, match):
        """
        Test a dict value for inequality.
        :param match: User-given value to compare against
        """
        return self.proc_test(
            lambda value: value != match,
            ('!=', self._field_path, hashable(match))
        )

    def __lt__(self, match):
        """
        Test a dict value for being lower than another value.
        :param match: User-given value to compare against
        """
        return self.proc_test(
            lambda value: value < match,
            ('<', self._field_path, match)
        )

    def __le__(self, match):
        """
        Test a dict value for being lower than or equal to another value.
        :param match: User-given value to compare against
        """
        return self.proc_test(
            lambda value: value <= match,
            ('<=', self._field_path, match)
        )

    def __gt__(self, match):
        """
        Test a dict value for being greater than another value.
        :param match: User-given value to compare against
        """
        return self.proc_test(
            lambda value: value > match,
            ('>', self._field_path, match)
        )

    def __ge__(self, match):
        """
        Test a dict value for being greater than or equal to another value.
        :param match: User-given value to compare against
        """
        return self.proc_test(
            lambda value: value >= match,
            ('>=', self._field_path, match)
        )

    def exists(self):
        """
        Test for a dict where a provided key exists.
        """
        return self.proc_test(
            lambda _: True,
            ('exists', self._field_path)
        )

    def search(self, regex: str, flags: int = 0):
        """
        Run a regex test for a dict value.
        :param regex: The regular expression to use for matching
        :param flags: regex flags to pass to re.match
        """

        def test(value):
            if not isinstance(value, str):
                return False

            return re.search(regex, value, flags) is not None

        return self.proc_test(test, ('search', self._field_path, regex))

    def test(self, func):
        """
        Run a user-defined test function against a dict value.
        :param func: The function to call, passing the dict as the first
                     argument
        :param args: Additional arguments to pass to the test function
        """
        return self.proc_test(
            lambda value: func(value),
            ('test', self._field_path, func)
        )
