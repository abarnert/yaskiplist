# yaskiplist
Yet another skiplist implementation

The primary purpose of this library is to let me play around with
different APIs for sorted collections, to get an idea of what kind
of operations should be part of a mutable sorted mapping ABC.

The secondary purpose is to let me play around with different
optimizations (which is why I use a skiplist rather than a red-black
tree or something else more complicated)--which means that what's 
checked in at any given moment may contain pessimizations, or at
least code that's more complex without being faster or smaller.

But if you want to actually _use_ it, despite all that (notice 
that there are plenty of sorted collections on PyPI based on 
skiplists,various kinds of trees, and even implementations that
switch from one data structure to another dynamically), I can't
stop you.

The type `skiplist.SkipList` is a `MutableMapping`. All `dict`-like
operations work as you'd expect (including, I hope, construction). 
Beyond that:

* Iteration always goes in sorted order.
* `pop` always pops the lowest element.
* `multipop` allows popping K elements at once (more efficiently
  than calling `pop` K times, which might be useful for a pqueue?)
* You can look up key slices: `d[lo:hi]` returns an iterable of
  all values for which `lo <= k < hi`. (At the moment, it returns
  a list. It should return a smart value view, but I haven't
  written those.)
* `dump` will print out the skiplist structure, so you can see
  how degenerate your skiplist is, or debug any problems, as long
  as your collection is pretty small.

Ideas to play with:

* Get the benchmarks working. And test on PyPy, not just CPython.
* Is limiting the height to 31 really worth doing? The odds of
  any insert breaking that limit are 1/4B, and the cost of doing
  so is not that big a deal.
* Does limiting each insert to only bump the current height by
  one do anything? I've seen multiple implementations do this. Is
  it a good optimization for small collections?
* Some API for customizing `p`? (Should a user have to work it
  out or dig up a table? I think users would be most interested
  in reducing space; if they could specify at most 1.08 average
  pointers/node, we could set p=1/16 and let them know that the
  actual average is 1.072, and average search times are 2.0x
  longer than default. I think the rule is to pick the next
  integer power of 2 such that 1/(1-p) < requested average.
  Except that isn't quite right; you want 1/16, 1/8, 1/4, 5/16,
  11/32, 23/64, ..., 1/e, or something like that? Go dig up the
  paper and find out. Anyway, if 1/e minimizes time, why is
  1/2, which uses more pointers, the usual default? Maybe just
  lower variability, meaning it's less likely to be degenerate
  for small collections?
* Factor out common bits of the three core methods (i.e., make
  `_find` usable by set/del, not just get).
* Re-simplify the nested loop code, since making it harder to 
  read didn't make it any faster.
* Slice assignment? (Obviously only same-size iterables.)
* Dual to `multipop`--basically, an `update` variant that assumes
  sorted keys. (And should `update` automatically defer to that
  if given another `SkipList` or `SortedMapping`?)
* Use `multipop` and `update_sorted` or whatever to implement
  a priority queue and see how well it works. (Although really,
  the only reason I know of to prefer a skiplist with combined ops 
  as a pqueue is for low-contention parallel scheduling, and
  building a useful test suite that fakes problems with 
  parallelism on top of the GIL is probably not worth it...)
* Sorted sets.
* Smart views. `keys` and `items` are sorted sets.
* An API to get sliced keys and items, not just values. Although
  if `d.keys()` is a sorted set and `d.keys()[lo:hi]` works, maybe
  that's sufficient?
* Add width tracking for logarithmic indexing (and what does
  that allow for reversed iteration?). Play with different APIs
  for using this ("sequence views" `d.keyseq()[13]` and 
  `d.itemsseq()[-9:-5]`; `d.by_index[13:17]`; ...). Does this 
  make `values` a sequence? Does it mean `keys` and `items` are 
  sequences and sets at the same time? Is there a `SortedSet` API 
  to be written that makes sense of that? Does that mean there's a 
  `MutableSortedSet` that is a `MutableSet` and a `Sequence` but 
  not a `MutableSequence`?
* Maybe change this into a simple skiplist, and a wrapper to
  turn a simple sorted mapping into a fancy one? That wrapper might
  be useful for experimenting with other collections from PyPI, but
  ultimately, a better design would be an ABC-and-mixin.
* How much (if any) efficiency comes from replacing the `__slots__`
  based `Node` (with key, value, and list of pointers) with a flat
  list (where the key and value are the first two elements)?
* `key` and `reverse` parameters? Making that work efficiently
  (not wasting space for `key(k)` in every node) without
  conditional code all over the place would probably be a
  nightmare; a better answer may be a variation on PEP 455, but
  specifically for sorted dicts. (And maybe multiple variations:
  one that stores `key(k): (k, v)`, one that requires an
  invertible transformation and just stores `key(k)` but calls
  `unkey` on fetches, one that just doesn't preserve `k`, ...)
* A hash+skiplist (i.e., just storing the nodes in a dict) can make
  `__getitem__` O(1), but at what constant-factor time and space
  cost?
* Do back links add anything (even simplifying the factored-out
  `_find`) other than `__reversed__`? Does a full stack of back
  links instead of just one add anything at all? I don't think so,
  but... think it through.
* Combining the last two: could a hash plus back links speed up
  mutation as well as search?
* Look over all of the other skiplist and general sorted collection
  libs on PyPI to see what they all do.
