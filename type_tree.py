from typing import List, Tuple, Dict, Set, Any, Callable
from utils import AttributedTree, parse_template_apply


class TypeTree(AttributedTree):
    def __init__(self, tree: AttributedTree):
        #TODO validate the tree
        #TODO build the tree
        pass

    def get_init_term(self) -> AttributedTree:
        #TODO
        pass
    
    def de_init(self) -> "TypeTree":
        #TODO
        pass

    def is_enum_type(self) -> bool:
        if not self.has_attribute("alias"):
            raise Exception("Unnormalized type tree")
        
        return self.name == "enum_type"

    @staticmethod
    def validate(tree: "TypeTree") -> bool:
        #TODO
        pass
    
    @staticmethod
    def reduce(type_trees: "List[TypeTree]") -> "TypeTree":
        #TODO
        pass

    @staticmethod
    def build_strcut_type(fields: "List[str]", type_trees: "List[TypeTree]") -> "TypeTree":
        #TODO
        pass

    @staticmethod
    def build_array_type(type_trees: "List[TypeTree]") -> "TypeTree":
        #TODO
        pass

    @staticmethod
    def build_map_type(type_trees: "List[TypeTree]") -> "TypeTree":
        #TODO
        pass

    @staticmethod
    def build_enum_type(alias: str) -> "TypeTree":
        #TODO assign the `alias` attribute
        pass

    @staticmethod
    def build_tuple_type(type_trees: "List[TypeTree]") -> "TypeTree":
        #TODO
        pass

    def get_coercion(self, another_type: "TypeTree") -> Callable[[str], str]:
        #TODO
        pass

    def get_s11n_code(self) -> Tuple:
        #TODO
        pass

    def __le__(self, another_type: "TypeTree") -> bool:
        #TODO
        pass

    def __ge__(self, another_type: "TypeTree") -> bool:
        #TODO
        pass

def get_int_type():
    return TypeTree(AttributedTree("int"))

def get_bool_type():
    return TypeTree(AttributedTree("bool"))

def get_real_type():
    return TypeTree(AttributedTree("real"))

def get_char_type():
    return TypeTree(AttributedTree("char"))

def is_type(type_tree: TypeTree) -> bool:
    #TODO
    pass

def get_term_type(term_tree: AttributedTree) -> TypeTree | None:
    #TODO
    #TODO require is_type
    pass