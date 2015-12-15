import collections
import random

class Node:
    # TODO: It would save a bit of memory, and might be faster,
    # to collapse this into a single list where n[0] is key,
    # n[1] is value, n[2:] is nexts. Is the benefit worth the
    # extra complexity?
    __slots__ = ['key', 'value', 'nexts']
    def __init__(self, key, value, level):
        self.key, self.value = key, value
        self.nexts = [None for _ in range(level)]

class SkipList(collections.abc.MutableMapping):
    # TODO: key and reverse arguments? Of course that means
    # storing both key(k) and k for each node
    def __init__(self, *args, **kw):
        self.root = None
        self.len = 0
        if args or kw:
            self.update(*args, **kw)

    def __str__(self):
        return '{' + ', '.join('{}: {}'.format(k, v) for k, v in self.items()) + ')'

    def __repr__(self):
        return '{}({})'.format(type(self).__name__, self)

    def __iter__(self):
        cur = self.root
        while cur:
            yield cur.key
            cur = cur.nexts[0]

    def __len__(self):
        return self.len

    def __reversed__(self):
        raise TypeError('Cannot reverse a mapping')

    def __setitem__(self, key, value):
        level = 1
        while random.random() < 0.5:
            level += 1
        #print('new level', level)
        node = Node(key, value, level)
        #print(node.nexts)
        if not self.root:
            #print('new root')
            self.root = node
            self.len += 1
            return
        cur = self.root
        cur.nexts.extend(None for _ in range(level - len(cur.nexts)))
        for curlevel in reversed(range(level)):
            #print('level', curlevel)
            while cur.nexts[curlevel]:
                #print(cur.key, cur.nexts[curlevel].key)
                if cur.nexts[curlevel].key == key:
                    cur.value = value
                    #print('found')
                    return
                elif cur.nexts[curlevel].key > key:
                    #print('past value on level, backtrack and down')
                    break
                cur = cur.nexts[curlevel]
            if curlevel <= level:
                #print('insert on level')
                node.nexts[curlevel], cur.nexts[curlevel] = cur.nexts[curlevel], node
        self.len += 1

    def _find(self, key):
        if not self.root:
            return None, False
        if key < self.root.key:
            return None, False
        if key == self.root.key:
            return self.root, True
        cur = self.root
        for level in reversed(range(len(cur.nexts))):
            while cur.nexts[level]:
                if cur.nexts[level].key == key:
                    return cur.nexts[level], True
                elif cur.nexts[level].key > key:
                    break
                cur = cur.nexts[level]
        return cur, False

    def _getslice(self, keylo, keyhi):
        lo, _ = self._find(keylo)
        if not lo:
            lo = self.root
        while lo and lo.key < keyhi:
            if lo.key >= keylo:
                yield lo.value
            lo = lo.nexts[0]

    def _getitem(self, key):
        node, found = self._find(key)
        if found:
            return node.value
        raise KeyError(key)
        
    def __getitem__(self, key):
        # TODO: [lo:hi] is nice, but it would be great if it were a
        # view rather than a list. But then that view can't be Sized
        # (at least not with a probabilistic skiplist--maybe we could
        # provide a length hint, but not a very useful one). Being
        # reversible, on the other hand, is easy; it just requires a
        # _find on hi as well as on lo. That also means we could
        # handle a step of -1 here, although I don't know of any other
        # collections that allow a step of -1, but not any other value.
        # Meanwhile, being able to ask for sliced key, value, and item
        # views would be great. Or maybe just make the views sliceable?
        # Although d.values()[7:13] when 7 and 13 are keys rather than
        # values seemsvery wrong. But what about d.values[7:13]? Or
        # is that too misleading? See what the various tree and skiplist
        # libs on PyPI do...
        if isinstance(key, slice):
            if key.step not in (None, 1):
                raise KeyError('{} cannot get extended slices'.format(type(self).__name__))
            return list(self._getslice(key.start, key.stop))
        return self._getitem(key)

    def __delitem__(self, key):
        # TODO: if _find returned the node _before_ the current
        # node at its highest level, we could use that here, and
        # presumably in __setitem__ as well.
        if not self.root:
            raise KeyError(key)
        if key < self.root.key:
            raise KeyError(key)
        if key == self.root.key:
            next = self.root.nexts[0]
            if next:
                next.nexts.extend(self.root.nexts[len(next.nexts):])
            self.root = next
            self.len -= 1
            return
        cur = self.root
        found = False
        for level in reversed(range(len(cur.nexts))):
            while cur.nexts[level]:
                if cur.nexts[level].key == key:
                    found = True
                    cur.nexts[level] = cur.nexts[level].nexts[level]
                    break
                elif cur.nexts[level].key > key:
                    break
                cur = cur.nexts[level]
        if not found:
            raise KeyError(key)
        self.len -= 1

    # TODO: pop just happens to always pop the smallest value.
    # Do we want to make that an API guarantee? Do we need a
    # pop_right?

    def multipop(self, k):
        cur = self.root
        items = []
        for _ in range(k):
            items.append((cur.key, cur.value))
            cur = cur.nexts[0]
            if not cur:
                break
        if cur:
            for level in range(len(cur.nexts), len(self.root.nexts)):
                # TODO: Can we save next across levels, so this is
                # O(k + newlevels) instead of O(k * newlevels)? I
                # think we just have to back up one step at each level?
                next = self.root.nexts[level]
                while next and next.key <= cur.key:
                    next = next.nexts[level]
                cur.nexts.append(next)
        self.root = cur
        return items

    # TODO: A special-case update for use with already-sorted
    # kv pairs (or a SkipList or RBTree or a sorted OrderedDict)
    # could be much more efficient than plain update.

    # TODO: A skiplist can do indexing in logarithic time if you
    # store the link width for each node's highest link. Do we want
    # that? If so, with what API? __getitem__ obviously collides
    # with keys that happen to be integers. Maybe d.by_index[3]?
    # Or maybe we want a sequence view d.seq()? Meanwhile, if we
    # have sequence-like behavior, what about the index method?

    def dump(self):
        if not self.root:
            return
        for level in reversed(range(len(self.root.nexts))):
            print('level {}: '.format(level), end='')
            cur = self.root
            while cur:
                print(cur.key, end=' ')
                cur = cur.nexts[level]
            print()
    
