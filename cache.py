#!/usr/bin/env python
""" Implements generic caching as well as a caching decorator. """

__author__ = "Johannes Stuettgen <johannes.stuettgen@gmail.com>"

def lru_cache(func, maxsize=None):
    """ Decorator to use LRUCache on function arguments.

    If maxsize is not provided we use a Python dict instead,
    to provide an infinite cache. This can cause the Python process
    to run out of memory and crash.

    However, it allows for simple memoization of functions.
    """
    if maxsize:
        cache = LRUCache(maxsize)
    else:
        cache = {}
    def cached_func(*args, **kwargs):
        key = (args, tuple(kwargs.items()))
        if key in cache:
            return cache[key]
        cache[key] = func(*args, **kwargs)
        return cache[key]
    return cached_func

class LRUCache(object):
    """ Implements a last recently used cache in pure Python.

    The cache has a 'maxsize'. If you don't need this you also won't
    need the LRU property so just use a Python dict.

    The cache operates a queue, implemented as a linked list.
    Whenever an item is retrieved from the cache, it is bumped to the
    top of the queue. If an insertion exceeds the capacity, the item
    at the end of the queue is evicted.

    To facilitate O(1) cache retrieval we also operate a hash map
    (implemented as a Python dict), which is used to look up items by key.
    """
    def __init__(self, maxsize):
        self.cache = {}
        self.queue = None
        self.size = 0
        self.maxsize = maxsize

    def _update_node(self, node):
        """ Push a node to beginning of queue. """
        if self.queue:
            if node is not self.queue:
                node.unlink()
                self.queue.prepend(node)
        self.queue = node

    def _delete_oldest(self):
        """ Delete oldest item from cache. """
        if self.queue:
            node = self.queue.prev
            del self.cache[node.key]
            node.unlink()
            self.size -= 1

    def __getitem__(self, key):
        node = self.cache[key]
        self._update_node(node)
        return node.value

    def __setitem__(self, key, value):
        node = ListHead(key, value)
        self.cache[key] = node
        self._update_node(node)
        self.size += 1
        if self.size > self.maxsize:
            self._delete_oldest()

    def __contains__(self, key):
        return key in self.cache

    def __iter__(self):
        """ Iterator over the cache in order of use. """
        node = self.queue
        while node:
            yield node.key
            node = node.next

    def iteritems(self):
        node = self.queue
        while node:
            yield (node.key, node.value)
            node = node.next

    def items(self):
        result = []
        if not self.queue:
            return result
        result.append((self.queue.key, self.queue.value))
        node = self.queue.next
        while node is not self.queue:
            result.append((node.key, node.value))
            node = node.next
        return result

    def __len__(self):
        return self.size

class ListHead(object):
    """ A circular, doubly linked, list for storing key/value pairs.
    Normally, a linked list is a bad idea in Python so I didn't put this into
    its own module. However, this is the most efficient way to implement the
    maxsize property for a cache.

    Note: I didn't use collections.deque, because I couldn't find a way to
    manually relink nodes in the list and keep references to the internal list
    nodes for efficient integration into the hashmap.
    """
    def __init__(self, key=None, value=None):
        self.prev = self
        self.next = self
        self.key = key
        self.value = value

    def unlink(self):
        """ Remove a node from a list. """
        if self.prev and self.prev is not self:
            self.prev.next = self.next
        if self.next and self.next is not self:
            self.next.prev = self.prev

    def append(self, node):
        """ Insert a new node after this one. """
        if self.next:
            self.next.prev = node
            node.next = self.next
        node.prev = self
        self.next = node

    def prepend(self, node):
        """ Insert a new node in front of this one. """
        if self.prev:
            self.prev.next = node
            node.prev = self.prev
        self.prev = node
        node.next = self

def test_lrucache():
    test_keys = range(10)
    test_values = [x * 10 for x in test_keys]
    test_data = zip(test_keys, test_values)
    cache = LRUCache(len(test_data))
    # Check if it retains the correct values if we fill it to capacity.
    for key, value in test_data:
        cache[key] = value
    for key, value in test_data:
        assert cache[key] == value
    # Now see if we can iterate over items in the cache
    # Note that the order is reversed because of the LRU property
    assert cache.items() == list(reversed(test_data))
    for cache_tuple, test_tuple in zip(cache.iteritems(), reversed(test_data)):
        assert cache_tuple == test_tuple
    for cache_key, test_key in zip(cache, reversed(test_keys)):
        assert cache_key == test_key
    # Now see if an item gets evicted if we insert something to exceed capacity.
    cache["foo"] = "test"
    assert cache["foo"] == "test"
    assert "foo" in cache
    assert 0 not in cache
    # Check if the queue correctly updates the lru for an item.
    # 1 is next to be evicted, but because we access it 2 gets evicted instead.
    assert cache[1] == 10
    cache["bla"] = "howdi"
    assert 1 in cache
    assert 2 not in cache
    print "LRUCache tests completed successfully!"

if __name__ == "__main__":
    test_lrucache()
