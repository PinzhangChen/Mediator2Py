import lark
from utils import AttributedTree, DirectedGraph
from typing import List, Set, Dict, Tuple, Any, Callable
from queue import Queue
from type_tree import TypeTree, get_term_type, is_type
from translator import ResolvedTerm

class TypeContext:
    def __init__(self):
        self._identifiers = {} # key: identifier ; value: one of "enum" (enum type), "type" (types except enums), "template" (template value argument), "sign" (signature), "local" (local variable), "inter" (internal nodes)
        self._type_aliases = {}
        self._template_args = {}
        self._signature = {}
        self._local_vars = {}
        self._internal_nodes = {}
    
    def is_var(self, name: str) -> bool:
        #TODO
        pass

    def type_of_var(self, var_name: str) -> TypeTree:
        #TODO
        pass

    def get_type(self, type_alias: str) -> Tuple[TypeTree, str]:
        '''
        Pay attention!
        '''
        if type_alias not in self._type_aliases:
            raise Exception #TODO
        
        return self._type_aliases[type_alias], self._identifiers[type_alias]
    
    def set_type(self, type_alias : str, type_tree : AttributedTree):
        if type_alias in self._identifiers:
            raise NameError(f"Type alias {type_alias} already existed.")
        
        if type_tree.name == "enum":
            self._identifiers.update({type_alias : "enum"})
        
        else:
            self._identifiers.update({type_alias : "type"})
        
        self._type_aliases.update({type_alias : type_tree.deepcopy()})
    
    def get_template_arg(self, arg_name: str):
        if arg_name not in self._template_args:
            raise NameError(f"Template argument {arg_name} not found.", name=arg_name)
        
        return self._template_args[arg_name]
    
    def set_signature(self, signature: Dict[str, Tuple[TypeTree, str | None]]):
        for param_name in signature:
            type_tree, IO = signature[param_name]
            self.set_param_type(param_name, type_tree, IO)
    
    def set_template_arg(self, arg_name: str, arg_val: AttributedTree):
        if arg_name in self._identifiers:
            raise NameError(f"Name {arg_name} already existed.", name=arg_name)
        
        self._identifiers.update({arg_name : "template"}) #TODO: deepcopy?
        self._template_args.update({arg_name : arg_val.deepcopy()})

    def get_param_type(self, param_name: str, with_IO: bool = False):
        if param_name not in self._signature:
            raise NameError(f"Parameter '{param_name}' not found.", name=param_name)
        
        if with_IO:
            return self._signature["param_name"]
        else:
            return self._signature["param_name"][0]

    def set_param_type(self, param_name: str, type_tree: AttributedTree, IO: str | None = None):
        if param_name in self._identifiers:
            raise NameError(f"Parameter '{param_name}' already existed.", name=param_name)
        
        self._identifiers.update({param_name : "sign"})
        self._signature.update({param_name : (type_tree.deepcopy(), IO)})

    def set_local_var_type(self, var_name: str, type_tree: TypeTree):
        if var_name in self._identifiers:
            raise NameError(f"Name '{var_name}' already existed.")
        
        self._identifiers.update({var_name: "local"})
        self._local_vars.update({var_name: type_tree.copy()})
    

    def instantiate_type(self, type_tree: AttributedTree) -> AttributedTree:
        '''
        Warning: This is in-place.
        '''
        queue = Queue()
        queue.put(type_tree)
        
        while True:
            if queue.empty():
                break

            current_tree = queue.get()

            for i in range(current_tree.n_children):
                child = current_tree.children[i]
                if child.name == "IDENTIFIER":
                    current_tree[i] = self.get_type(child.attributes["value"])
                else:
                    queue.put(child)
            
            if current_tree.name == "bounded_int":
                l = current_tree.attributes["l"]
                if isinstance(l, str):
                    template_arg = self.get_template_arg(l)
                    assert template_arg.name == "VALUE"
                    l = template_arg.attributes["value"]
                assert isinstance(l, int)
                current_tree.attributes["l"] = l

                r = current_tree.attributes["r"]
                if isinstance(r, str):
                    template_arg = self.get_template_arg(r)
                    assert template_arg.name == "VALUE"
                    r = template_arg.attributes["value"]
                assert isinstance(r, int)
                current_tree.attributes["r"] = r
            
            if current_tree.name == "array_type":
                length = current_tree.attributes["length"]
                if isinstance(length, str):
                    template_arg = self.get_template_arg(length)
                    assert template_arg.name == "VALUE"
                    length = template_arg.attributes["value"]
                assert isinstance(length, int)
                current_tree.attributes["length"] = length

            #TODO: assumption: "term" of initialized type need not to be instantiated (only need to generate their code directly)
    
    def instantiate(self, type_tree: AttributedTree, in_place: bool = False) -> TypeTree | None:
        #TODO
        pass

    def is_determined_term(term_tree: AttributedTree) -> bool:
        #TODO
        pass

    def copy(self):
        #TODO
        pass

    def is_enum_type(self, name: str) -> bool:
        return name in self._identifiers and self._identifiers[name] == "enum"
    
    def is_port(self, name: str, IO: str = "") -> bool:
        if IO == "":
            return name in self._signature

        return name in self._signature and self._signature[name][1] == IO
    
    def set_internal_node(self, name: str):
        #TODO
        pass
    
    def get_internal_node_status(self, name: str) -> bool:
        '''
        Warning: This has side-effect
        '''
        #TODO
        pass


class TemplateManager:
    #TODO
    def __init__(self, type_context: TypeContext):
        #TODO
        self._type_context = type_context
        self._data: Dict[str, TemplateDatum]
    
    def query(self, expansion_request: "ExpansionRequest", raise_exception: bool = True) -> "ExpansionDatum":
        name = expansion_request.name
        template_args = expansion_request.template_args
        if name not in self._data:
            raise NameError(f"'{name}' is not a valid object name.")
        
        return self._data[name].query(template_args, raise_exception)

    def create(self, expansion_request: "ExpansionRequest"):
        name = expansion_request.name
        template_args = expansion_request.template_args
        if name not in self._data:
            raise NameError(f"'{name}' is not a valid object name.")
        
        return self._data[name].create(template_args)
    
    def query_or_create(self, expansion_request: "ExpansionRequest"):
        name = expansion_request.name
        template_args = expansion_request.template_args
        if name not in self._data:
            raise NameError(f"'{name}' is not a valid object name.")
        
        return self._data[name].query_or_create(template_args)
    
    def get_signature_string(self, name: str) -> str:
        if name not in self._data:
            raise NameError(f"'{name}' is not a valid object name")
        
        return self._data[name]._signature_form.__str__()

class TemplateDatum:
    def __init__(self, name: str, type_context: TypeContext, template_form: "TemplateForm", signature_form: "SignatureForm"):
        #TODO
        self._name = name
        self._type_context = type_context
        self._template_form = template_form
        self._signature_form = signature_form
        self._expansion_data: List[ExpansionDatum] = []

    def query(self, template_args: List[AttributedTree], raise_exception: bool = True) -> "ExpansionDatum" | None:
        for expansion_datum in self._expansion_data:
            if expansion_datum.template_args == template_args:
                return ExpansionDatum
        
        if raise_exception:
            raise Exception #TODO
        else:
            return None
    
    def create(self, template_args: List[AttributedTree]) -> "ExpansionDatum" | None:
        if self.query(template_args, raise_exception=False) != None:
            raise Exception
        
        context = self._type_context.copy()

        # Prepare the context for signature instantiation.
        self._template_form.transform(context, template_args)

        # Instantiate the signature
        expanded_signature = self._signature_form.instantiate(context)

        # Expand the context
        context = expanded_signature.transform(context)

        # Create the expansion datum
        expansion_datum = ExpansionDatum(template_args, expanded_signature, context, f"m_{len(self._expansion_data)}_{self._name}")
        self._expansion_data.append(expansion_datum)
        return expansion_datum
    
    def query_or_create(self, template_args: List[AttributedTree]) -> "ExpansionDatum":
        result = self.query(template_args, raise_exception=False)

        if result:
            return result
        
        return self.create(template_args)

class ExpansionDatum:
    def __init__(self, template_args: List[AttributedTree], expanded_signature: "SignatureForm", expanded_context: TypeContext, actual_name: str):
        self._template_args = template_args
        self._expanded_signature = expanded_signature
        self._expanded_context = expanded_context
        self._actual_name = actual_name

    @property
    def template_args(self) -> List[AttributedTree]:
        return self._template_args.copy()

    @property
    def expanded_context(self) -> TypeContext:
        return self._expanded_context.copy() 
    
    @property
    def expanded_signature(self) -> "SignatureForm":
        return self._expanded_signature

    @property
    def actual_name(self) -> str:
        return self.actual_name
    
    def new_connection_table(self) -> "ConnectionTable":
        return self._expanded_signature.new_connection_table(self._actual_name)

class TemplateForm:
    def __init__(self, data: List[Tuple[str, TypeTree | None]]):
        self._data = data

    def validate(self, arg_types: List[TypeTree | None]):
        expected_len = len(self._data)
        actual_len = len(arg_types)
        if actual_len != expected_len:
            raise Exception #TODO
        
        for i in range(expected_len):
            expected_type = self._data[i][1]
            actual_type = arg_types[i]
            if not actual_type <= expected_type:
                raise Exception
    
    def transform(self, type_context: TypeContext, template_args: List[AttributedTree]):
        # validate the arguments
        arg_types = list([get_term_type(arg) for arg in template_args])
        self.validate(arg_types)
        
        for i in range(len(template_args)):
            arg = template_args[i]
            arg_name = self._data[i][0]
            if is_type(arg): # type parameter
                type_context.set_type(arg_name, arg)
            else: # value parameter
                type_context.set_template_arg(arg_name, arg)
    
        

class ExpansionRequest:
    def __init__(self, name: str, template_args: List[AttributedTree]):
        self._name = name
        self._template_args = template_args
    
    @property
    def name(self):
        return self._name
    
    @property
    def template_args(self):
        return self._template_args #TODO

class SignatureForm:
    def __init__(self, data: List[Tuple[str, TypeTree, str | None]]):
        self._data = data
    
    def is_function(self) -> bool:
        return self._data[-1][0] == "!"

    def transform(self, type_context: TypeContext):
        type_context.set_signature(dict({x[0]: (x[1], x[2]) for x in self._data}))
    
    def validate(self, arg_types: List[TypeTree]):
        if self.is_function():
            expected_len = len(self._data) - 1
        else:
            expected_len = len(self._data)
        
        if len(arg_types) != expected_len:
            raise Exception #TODO
        
        if not all([arg_types[i] <= self._data[i][1] for i in range(expected_len)]):
            raise Exception
    
    def instantiate(self, type_context: TypeContext) -> "SignatureForm":
        new_data = []
        for old_datum in self._data:
            new_datum = (old_datum[0], type_context.instantiate(old_datum[1]), old_datum[2])
            new_data.append(new_datum)
        
        return SignatureForm(new_data)
    
    def get_return_type(self) -> TypeTree:
        if not self.is_function():
            raise Exception #TODO
        
        return self._data[-1][1].copy()
    
    def validate_and_convert(self, terms_resolved: List[ResolvedTerm]) -> ResolvedTerm:
        expected_len = len(self._data - 1)
        actual_len = len(terms_resolved)

        if actual_len != expected_len:
            raise Exception #TODO
        
        all_expansion_requests = []
        python_codes = []
        for i in range(expected_len):
            term_resolved = terms_resolved[i]

            python_code = term_resolved.python_code
            type_tree = term_resolved.type_tree
            expansion_requests = term_resolved.expansion_requests
            
            coercion = type_tree.get_coercion(self._data[i][1])
            python_codes.append(coercion(python_code))
            all_expansion_requests += expansion_requests
        
        python_code = "(" + ", ".join(python_codes) + ")"

        return ResolvedTerm(python_code, self.get_return_type(), all_expansion_requests)
    
    def __str__(self):
        if self.is_function():
            expected_len = len(self._data) - 1
        else:
            expected_len = len(self.data)

        python_code = []
        for i in range(expected_len):
            python_code.append("id_" + self._data[i][0])

        return r"(" + ", ".join(python_code) + r")"
    
    def new_connection_table(self, actual_name: str) -> "ConnectionTable":
        if self.is_function():
            raise Exception
        
        connections = []
        for port_name, port_type, port_IO in self._data:
            connections.append([port_name, None])
        
        return ConnectionTable(actual_name, connections)

class ConnectionTable:
    def __init__(self, actual_name: str, connections: List[Tuple[str, str]]):
        self.actual_name = actual_name
        self.connections = connections
    
    def set_node(self, port_name: str, node_name: str):
        for i in range(len(self.connections)):
            if self.connections[i][0] == port_name:
                self.connections[i][1] = node_name
                return
        
        raise Exception("Port not found")
    
    def translate(self) -> str:
        python_code = []
        for port_name, port_arg in self.connections:
            python_code.append("id_" + port_arg)
        python_code = ", ".join(python_code)

        python_code = self.actual_name + r"(" + python_code + r")"

        return python_code
    
    def copy(self) -> str:
        new_connnections = []
        for connection in self.connections:
            new_connection = (None, None)
            new_connection[0] = connection[0]
            new_connection[1] = connection[1]
            new_connnections.append(new_connection)
        
        return ConnectionTable(self.actual_name, new_connnections)