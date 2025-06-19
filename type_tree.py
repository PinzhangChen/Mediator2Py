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

    def get_coercion(self, another_type: "TypeTree") -> Any:
        _t1 = self.de_init()
        _t2 = another_type.de_init()

        if _t2.name == "union":
            for i in range(len(_t2.children)):
                t = _t2.children[i]
                coercion = _t1.get_coercion(t)
                if coercion != None:
                    break
            
            if coercion != None:
                return ("inj", i, coercion)
            
            return None
        
        if _t1.name == "int":
            if _t2.name == "int":
                return ("direct")
            
            if _t2.name == "bounded_int":
                return ("bounded", _t2.get_attribute("l"), _t2.get_attribute("r"))
            
            if _t2.name == "real":
                return ("direct")
            
            return None
        
        if _t1.name == "bounded_int":
            if _t2.name == "int":
                return ("direct")
            
            if _t2.name == "bounded_int":
                return ("bounded", _t2.get_attribute("l"), _t2.get_attribute("r"))
            
            if _t2.name == "real":
                return ("direct")
            
            return None
        
        if _t1.name == "real":
            if _t2.name == "real":
                return ("direct")
            
            return None
        
        if _t1.name == "bool":
            if _t2.name == "int":
                return ("direct")
            
            if _t2.name == "bounded_int":
                return ("direct")
            
            if _t2.name == "real":
                return ("direct")
            
            if _t2.name == "bool":
                return ("direct")
            
            return None
        
        if _t1.name == "char":
            if _t2.name == "char":
                return ("direct")
            
            return None
        
        if _t1.name == "IDENTIFIER":
            _t1_enum_name = _t1.get_attribute("value")
            
            if _t2.name != "IDENTIFIER":
                return None
            
            _t2_enum_name = _t2.get_attribute("value")

            if _t1_enum_name != _t2_enum_name:
                return None
            
            return ("direct")
        
        if _t1.name == "tuple":
            if _t2.name != "tuple":
                return None
            
            if _t1.n_children != _t2.n_children:
                return None
            
            coercions = []
            for i in range(_t1.n_children):
                _t1_comp = _t1.children[i]
                _t2_comp = _t2.children[i]
                coercion = _t1_comp.get_coercion(_t2_comp)
                
                if coercion == None:
                    return None
                
                coercions.append(coercion)
                
            return ("tuple", *coercions)
        
        if _t1.name == "union":
            coercions = []
            for i in range(_t1.n_children):
                _t1_comp = _t1.children[i]
                _t2_comp = _t2.children[i]
                coercion = _t1_comp.get_coercion(_t2_comp)
                
                if coercion == None:
                    return None
                
                coercions.append(coercion)
            
            return ("union", *coercions)
        
        if _t1.name == "array":
            if _t2.name == "array":
                _t1_len = _t1.get_attribute("length")
                _t2_len = _t2.get_attribute("length")

                if int(_t2_len) < int(_t1_len):
                    return None
                
                _t1_entry = _t1.children[0]
                _t2_entry = _t2.children[0]

                coercion = _t1_entry.get_coercion(_t2_entry)

                if coercion == None:
                    return None
                
                return ("array", int(_t2_len), coercion)
            
            if _t2.name == "list":
                _t1_entry = _t1.children[0]
                _t2_entry = _t2.children[0]

                coercion = _t1_entry.get_coercion(_t2_entry)

                if coercion == None:
                    return None
                
                return ("list", coercion)
        
        if _t1.name == "list":
            if _t2.name != "list":
                return None
            
            _t1_entry = _t1.children[0]
            _t2_entry = _t2.children[0]

            coercion = _t1_entry.get_coercion(_t2_entry)

            if coercion == None:
                return None
            
            return ("list", coercion)
        
        if _t1.name == "map":
            if _t2.name != "map":
                return None
            
            _t1_key, _t1_val = _t1.children
            _t2_key, _t2_val = _t2.children

            key_coercion = _t1_key.get_coercion(_t2_key)
            val_coercion = _t1_val.get_coercion(_t2_val)

            if key_coercion == None or val_coercion == None:
                return None
            
            return ("map", key_coercion, val_coercion)
        
        if _t1.name == "struct":
            if _t2.name != "struct":
                return None
            
            _t1_fields = _t1.get_attribute("fields")
            _t2_fields = _t2.get_attribute("fields")
            _t1_fields_set = set(_t1_fields)
            _t2_fields_set = set(_t2_fields)

            if not _t2_fields_set.issubset(_t1_fields_set):
                return None
            
            coercions = []
            for _t2_field in _t2_fields:
                _t2_idx = _t2_fields.index(_t2_field)
                _t1_idx = _t1_fields.index(_t2_field)

                _t1_subtree = _t1.children[_t1_idx]
                _t2_subtree = _t1.children[_t2_idx]

                coercion = _t1_subtree.get_coercion(_t2_subtree)

                if coercion == None:
                    return None
                
                coercions.append((_t2_field, coercion))
            
            return ("struct", *coercions)
        
        raise TypeError

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