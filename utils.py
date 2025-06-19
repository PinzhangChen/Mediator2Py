import lark
import re
import os
from typing import Dict, List, Set, Tuple, Any, Callable
from queue import Queue

class TreeAttributes:
    def __init__(self, data: "Dict[str, int | float | bool | str | AttributedTree]" = {}):
        self._data = data
    
    def __getitem__(self, key: str) -> Any:
        return self._data[key]
    
    def __setitem__(self, key: str, val: "int | float | bool | str | AttributedTree"):
        conditions = [\
            isinstance(val, int),\
            isinstance(val, float),\
            isinstance(val, bool),\
            isinstance(val, str),\
            isinstance(val, "AttributedTree")
        ]
        
        if any(conditions):
            self._data[key] = val
        else:
            raise TypeError
    
    def copy(self):
        new_data = {}
        for key in self._data:
            val = self._data[key]
            if hasattr(val, "copy"):
                new_data.update({key: val.copy()})
            else:
                new_data.update({key: val})
        
        return TreeAttributes(new_data)

class AttributedTree:
    def __init__(self, name : str, attributes : TreeAttributes | Dict = TreeAttributes({}), children : "List[AttributedTree]" = []):
        self.name = name

        if type(attributes) == dict:
            attributes = TreeAttributes(attributes)
        self.attributes = attributes
        
        self.children = children
    
    def __str__(self):
        return f"Tree({self.name}, [" + ", ".join(list([str(child) for child in self.children])) + "])"
    
    def copy(self) -> "AttributedTree":
        stack_tree = [0, self]
        stack_children = [[], []]
        current_tree = self

        while True:
            if current_tree == 0:
                return stack_children[0][0]
            
            n_children_expected = len(current_tree.children)
            n_children_actual = len(stack_children[-1])

            if n_children_actual < n_children_expected:
                current_tree = current_tree.children[n_children_actual]
                stack_tree.append(current_tree)
                stack_children.append([])
                
                continue
            elif n_children_actual == n_children_expected:
                attr_tree = AttributedTree(current_tree.name, current_tree.attributes.copy(), stack_children[-1])

                stack_tree.pop()
                stack_children.pop()

                current_tree = stack_tree[-1]
                stack_children[-1].append(attr_tree)

                continue
            else:
                raise Exception(f"{n_children_actual}, {n_children_expected}")
    
    def deepcopy(self):
        '''
        Also copy keys of the attributes.
        '''
        stack_tree = [0, self]
        stack_children = [[], []]
        current_tree = self

        while True:
            if current_tree == 0:
                return stack_children[0][0]
            
            n_children_expected = len(current_tree.children)
            n_children_actual = len(stack_children[-1])

            if n_children_actual < n_children_expected:
                current_tree = current_tree.children[n_children_actual]
                stack_tree.append(current_tree)
                stack_children.append([])
                
                continue
            elif n_children_actual == n_children_expected:
                old_attributes = current_tree.attributes
                new_attributes = {}
                for key in old_attributes:
                    val = old_attributes[key]
                    if hasattr(val, "deepcopy"):
                        new_attributes.update({key : val.deepcopy()})
                    elif hasattr(val, "copy"):
                        new_attributes.update({key, val.copy()})
                    else:
                        new_attributes.update({key, val})
                
                attr_tree = AttributedTree(current_tree.name, new_attributes, stack_children[-1])

                stack_tree.pop()
                stack_children.pop()

                current_tree = stack_tree[-1]
                stack_children[-1].append(attr_tree)

                continue
            else:
                raise Exception(f"{n_children_actual}, {n_children_expected}")
    
    def __eq__(self, other):
        if not isinstance(other, AttributedTree):
            return False
        
        queue_self = Queue()
        queue_self.put(self)

        queue_other = Queue()
        queue_other.put(other)

        while True:
            if queue_self.empty() != queue_other.empty():
                return False
            
            if queue_self.empty():
                return True
            
            current_tree_self = queue_self.get()
            current_tree_other = queue_other.get()

            if current_tree_self.name != current_tree_other.name:
                return False
            
            if current_tree_self.attributes != current_tree_other.attributes:
                return False
            
            if len(current_tree_self.children) != len(current_tree_other.children):
                return False
            
            for i in range(len(current_tree_self.children)):
                queue_self.put(current_tree_self.children[i])
                queue_other.put(current_tree_other.children[i])

    @property
    def n_children(self):
        return len(self.children)
    
    def get_child_by_name(self, name: str, raise_exception: bool = True) -> "AttributedTree | None":
        '''
        Get the first child with the given name. Raise KeyError if the no such child exists.

        Be careful: change the child may effect this tree. So it's often a better practice to copy the result of this method.
        '''
        for child in self.children:
            if child.name == name:
                return child
        if raise_exception:
            raise KeyError(f"The tree '{self.name}' does not have the child '{name}'")
    
    def get_children_by_name(self, name:str, raise_exception: bool = True) -> "List[AttributedTree]":
        '''
        Get a list of children with the given name. Raise KeyError if no such child exists.

        Be careful: change the child may effect this tree. So it's often a better practice to copy the result of this method.
        '''
        result = []
        for child in self.children:
            if child.name == name:
                result.append(child)

        if result:
            return result
        
        if raise_exception:
            raise KeyError(f"The tree '{self.name}' does not have the child '{name}'")
        
        return []
    
    def get_attribute(self, name: str, raise_exception: bool = True):
        try:
            return self.attributes[name]
        except KeyError:
            if raise_exception:
                raise KeyError(f"'{name}' is not a valid attribute of the tree '{self.name}'")
            else:
                return None
            
    def has_attribute(self, name: str) -> bool:
        return name in self.attributes

class DFSManager:
    def __init__(self, tree: AttributedTree, node_operation: Callable[[AttributedTree, List], Any]):
        self._tree = tree
        self._node_operation = node_operation
        self._root_operation = lambda x : x
    
    def __init__(self, tree: AttributedTree, node_operation: Callable[[AttributedTree, List], Any], root_operation: Callable[[Any], Any]):
        self._tree = tree
        self._node_operation = node_operation
        self._root_operation = root_operation
    
    def run(self) -> Any:
        tree_stack = [0, self._tree]
        children_returns = [[], []]
        
        current_tree = self._tree
        while True:
            if current_tree == 0:
                return self._root_operation(children_returns[0][0])
            
            expected_n_children = current_tree.n_children
            actual_n_children = len(children_returns[-1])

            if actual_n_children < expected_n_children:
                current_tree = current_tree.children[actual_n_children]
                tree_stack.append(current_tree)
                children_returns.append([])
            elif actual_n_children == expected_n_children:
                tree_stack.pop()
                children_returns[-1].append(self._node_operation(current_tree, children_returns.pop()))
                current_tree = tree_stack[-1]
            else:
                raise Exception
        
class BFSManager:
    def __init__(self, tree: AttributedTree, pre_operation: Callable = lambda x : x, post_operation: Callable = lambda x : x):
        self._tree = tree
        self._queue: Queue[AttributedTree] = Queue()
        self._queue.put(tree)
        self._pre_operation = pre_operation
        self._post_operation = post_operation
    
    def run(self):
        while True:
            if self._queue.empty():
                break

            current_tree = self._queue.get()

            self._pre_operation(current_tree)

            for child in current_tree.children:
                self._queue.put(child)
            
            self._post_operation(current_tree)

class DirectedGraph:
    def __init__(self, nodes: Set[str] = set(), edges : List[Tuple[str, str]] = []):
        self.nodes = set()
        self.edges = []
        self.in_degrees = {}
        self.out_degrees = {}

        for node in nodes:
            self.add_node(self, node)
        
        for edge in edges:
            self.add_edge(self, edge)
    
    def add_node(self, node: str):       
        self.nodes.add(node)
        self.in_degrees.update({node : 0})
        self.out_degrees.update({node : 0})
    
    def add_edge(self, edge: Tuple[str, str]):
        src, tar = edge
        if src not in self.nodes or tar not in self.nodes:
            raise KeyError
        
        self.edges.append(edge)
        self.in_degrees[tar] += 1
        self.out_degrees[src] += 1
    
    def remove_edge(self, edge: Tuple[str, str]):
        src, tar = edge
        if src not in self.nodes or tar not in self.nodes:
            raise KeyError
        
        if edge not in self.edges:
            raise KeyError
        
        self.in_degrees[tar] -= 1
        self.out_degrees[src] -= 1
        
        self.edges.remove(edge)
    
    def remove_node(self, node: str):
        if node not in self.nodes:
            raise KeyError
        
        edges_to_del = []
        for edge in self.edges:
            src, tar = edge
            
            if node == src or node == tar:
                edges_to_del.append(edge)
        
        for edge in edges_to_del:
            self.remove_edge(edge)
        
        assert self.out_degrees[node] == self.in_degrees[node] == 0

        self.nodes.remove(node)
        self.in_degrees.pop(node)

    def copy(self) -> "DirectedGraph":
        return DirectedGraph(self.nodes.copy(), self.edges.copy())

    def topo_sort(self) -> List[str]:
        DAG_copy = self.copy()
        result = []

        while True:
            if DAG_copy.nodes == []:
                return result
            
            source_node = None
            for node in DAG_copy.in_degrees:
                if DAG_copy.in_degrees[node] == 0:
                    source_node = node
                    break
            
            if source_node is None:
                raise ValueError("Loop in a directed graph.")
            
            result.append(node)

            DAG_copy.remove_node(source_node)

def eval_placeholders(t : lark.Tree, tokens : List[Dict[str, Any]]) -> lark.Tree:
    '''
    This method evaluates the placeholders "Id@<id>" and "Val@<id>" in a Lark syntax tree. That is, those placeholders will be replaced with their actual value (stored in `tokens`).

    Be careful: This method is in-place.
    '''
    queue = Queue()
    queue.put(t)
    
    while True:
        if queue.empty():
            break
        
        current_tree = queue.get()
        
        if type(current_tree) == str:
            break
        elif type(current_tree) == lark.Token:
            token_type = current_tree.type
            token_value : str = current_tree.value
            if token_type == "IDENTIFIER" or token_type == "VALUE":
                idx = int(token_value.split("@")[1])
                current_tree.value = tokens[idx]["value"]
                continue
        elif type(current_tree) == lark.Tree:
            for child in current_tree.children:
                queue.put(child)
            continue

        raise TypeError

def get_symbol_name(t : lark.Tree | lark.Token | str) -> str:
    '''
    Get the name of a terminal or non-terminal in a Lark syntax tree.
    '''
    if isinstance(t, lark.Tree):
        return get_symbol_name(t.data)
    elif isinstance(t, lark.Token):
        assert t.type == "RULE"
        return t.value
    elif isinstance(t, str):
        return t
    else:
        raise TypeError
    
def Lark2AT(t : lark.Tree | lark.Token | str) -> AttributedTree:
    '''
    Transform a Lark tree to an AttributedTree. 
    '''
    current_tree = t
    stack_tree = [1, t]
    stack_children = [[], []]
    while True:
        assert len(stack_tree) == len(stack_children)

        if current_tree == 1:
            return stack_children[0][0]
        
        if type(current_tree) == str:
            attr_tree = AttributedTree(current_tree)
            stack_tree.pop()
            stack_children.pop()
            current_tree = stack_tree[-1]
            stack_children[-1].append(attr_tree)
            continue

        if type(current_tree) == lark.Token:
            token_type = current_tree.type
            token_value = current_tree.value
            if token_type == "IDENTIFIER" or token_type == "VALUE":
                attr_tree = AttributedTree(token_type, attributes={"value": token_value})
            else:
                attr_tree = AttributedTree(token_type)
            
            stack_tree.pop()
            stack_children.pop()
            current_tree = stack_tree[-1]
            stack_children[-1].append(attr_tree)
            continue

        if type(current_tree) == lark.Tree:
            n_children_expected = len(current_tree.children)
            n_children_actual = len(stack_children[-1])

            if n_children_actual < n_children_expected:
                current_tree = current_tree.children[n_children_actual]
                stack_tree.append(current_tree)
                stack_children.append([])
                continue
            elif n_children_actual == n_children_expected:
                attr_tree = AttributedTree(get_symbol_name(current_tree), children=stack_children[-1])
                
                stack_tree.pop()
                stack_children.pop()

                current_tree = stack_tree[-1]
                stack_children[-1].append(attr_tree)
                continue
            else:
                raise Exception
        
        raise TypeError(str(type(current_tree)) + get_symbol_name(stack_tree[-1]))


def parse_template_apply(template_apply: AttributedTree) -> List[AttributedTree]:
    #TODO
    assert template_apply.name == "template_apply"
    pass

def indent_code(python_code: str, level: int = 1) -> str:
    lines = re.split(r"\r\n|\r|\n", python_code)

    for i in range(len(lines)):
        lines[i] = "    " * level + lines[i]
    
    return "\n".join(lines)

def infer_original_name(actual_name: str) -> str:
    parts = actual_name.split("_")

    if re.match(r"\d", parts[1]):
        return "_".join(parts[2:])
    else:
        return "_".join(parts[1:])