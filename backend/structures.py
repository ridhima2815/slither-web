"""Hand-rolled doubly linked list used as the snake's body.

The head is the front of the list and the tail is the back, so a move is
push_front (new head) + pop_back (drop tail): both O(1), no array shifting.
"""
from __future__ import annotations

from typing import Any, Iterator, Optional


class Node:
    __slots__ = ("value", "prev", "next")

    def __init__(self, value: Any) -> None:
        self.value = value
        self.prev: Optional["Node"] = None
        self.next: Optional["Node"] = None


class DoublyLinkedList:
    def __init__(self) -> None:
        self.head: Optional[Node] = None
        self.tail: Optional[Node] = None
        self._size = 0

    def __len__(self) -> int:
        return self._size

    def __iter__(self) -> Iterator[Any]:
        """Yield values from head to tail."""
        node = self.head
        while node is not None:
            yield node.value
            node = node.next

    def push_front(self, value: Any) -> None:
        node = Node(value)
        if self.head is None:
            self.head = self.tail = node
        else:
            node.next = self.head
            self.head.prev = node
            self.head = node
        self._size += 1

    def pop_back(self) -> Any:
        if self.tail is None:
            raise IndexError("pop from empty DoublyLinkedList")
        node = self.tail
        self.tail = node.prev
        if self.tail is None:
            self.head = None
        else:
            self.tail.next = None
        node.prev = None
        self._size -= 1
        return node.value

    def clear(self) -> None:
        self.head = self.tail = None
        self._size = 0
