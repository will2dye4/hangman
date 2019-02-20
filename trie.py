from dataclasses import dataclass, field
from typing import Iterable, Dict, Optional, Sequence


@dataclass
class Node:
    value: str
    terminal: bool = False
    children: Dict[str, 'Node'] = field(init=False, default_factory=dict)

    def add_child(self, value: str, terminal: bool = False) -> 'Node':
        value = value.upper()
        if value in self.children:
            node = self.children[value]
        else:
            node = Node(value, terminal)
            self.children[value] = node
        return node

    def get_child(self, value: str) -> Optional['Node']:
        return self.children.get(value.upper())


class Trie:

    def __init__(self, items: Optional[Iterable[str]] = None) -> None:
        self.root = Node('')
        if items is not None:
            for item in items:
                self.add(item)

    def add(self, item: str) -> None:
        parent = self.root
        for letter in item.upper():
            child = parent.get_child(letter)
            if child is None:
                child = parent.add_child(letter)
            parent = child
        if parent != self.root:
            parent.terminal = True

    def get_node(self, prefix: str) -> Optional[Node]:
        parent = self.root
        for letter in prefix.upper():
            child = parent.get_child(letter)
            if child is None:
                return None
            parent = child
        return parent

    def suggest(self, prefix: str) -> Sequence[str]:
        prefix = prefix.upper()
        suggestions = []
        node = self.get_node(prefix)
        if node is None:
            return suggestions

        nodes = [(prefix, node)]
        while nodes:
            word, node = nodes.pop()
            if node.terminal:
                suggestions.append(word)
            for letter, child in node.children.items():
                nodes.append((word + letter, child))
        return suggestions

    def __contains__(self, item: str) -> bool:
        node = self.get_node(item)
        return node is not None and node.terminal
