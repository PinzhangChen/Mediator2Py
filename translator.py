from utils import AttributedTree, parse_template_apply, DFSManager, infer_original_name, indent_code
from queue import Queue
from template import TypeContext, TemplateManager, ExpansionRequest, ConnectionTable
from typing import List, Tuple, Set, Dict, Callable, Any
from enum import Enum
from type_tree import TypeTree, get_bool_type, get_int_type, get_char_type, get_real_type

class ObjectCategory(Enum):
    FUNCTION = 0
    AUTOMATON = 1
    SYSTEM = 2

class Translator:
    def __init__(self):
        self._type_context: TypeContext = TypeContext()
        self._buffer: List[str] = []
    
    def translate(self):
        pass

    @property
    def type_context(self):
        pass

class ProgramTranslator(Translator):
    def __init__(self, program_tree: AttributedTree):
        super().__init__()
        
        self._tree: AttributedTree = program_tree
        self._identifiers: Set[str]

        self._base_context: TypeContext
        self._function_data: Dict[str, AttributedTree]
        self._automaton_data: Dict[str, AttributedTree]
        self._system_data: Dict[str, AttributedTree]

        self._template_manager: TemplateManager
        self._expansion_requests: Queue[ExpansionRequest]
        
        self._buffer_head: str
        self._buffer_tail: str
        #TODO
    
    def translate(self) -> str: # Done
        '''
        Generate the python code.
        '''
        while True:
            if self._expansion_requests.empty():
                break
            
            request = self._expansion_requests.get()
            
            category = self.get_object_category(request.name)

            if category == ObjectCategory.FUNCTION:
                # Necessary data to generate the function code
                expansion_datum = self._template_manager.query(request)
                type_context = expansion_datum.expanded_context
                actual_name = expansion_datum.actual_name
                body = self.get_function_body(request.name)
                
                # Generate the function code
                python_code, new_requests = FunctionTranslator(type_context, actual_name, self._template_manager, body).translate()
            elif category == ObjectCategory.AUTOMATON:
                # Necessary data to generate the automaton code
                expansion_datum = self._template_manager.query(request)
                type_context = expansion_datum.expanded_context
                actual_name = expansion_datum.actual_name
                body = self.get_automaton_body(request.name)

                # Generate the automaton code
                python_code, new_requests = AutomatonTranslator(type_context, actual_name, self._template_manager, body).translate()
            elif category == ObjectCategory.SYSTEM:
                # Necessary data to generate the system code
                expansion_datum = self._template_manager.query(request)
                type_context = expansion_datum.expanded_context
                actual_name = expansion_datum.actual_name
                body = self.get_system_body(request.name)

                # Generate the system code
                python_code, new_requests = SystemTranslator(type_context, actual_name, self._template_manager, body).translate()
            else:
                raise Exception("Unknown exception. Maybe it is an upcoming feature.")
            
            # Add the code to buffer
            self._buffer.append(python_code)

            # Put new requests to the queue
            for new_request in new_requests:
                self._expansion_requests.put(new_request)

        return self._buffer_head + '\n\n'.join(self._buffer) + self._buffer_tail

    def get_object_category(self, name: str) -> ObjectCategory:
        if name in self._function_data:
            return ObjectCategory.FUNCTION
        
        if name in self._automaton_data:
            return ObjectCategory.AUTOMATON
        
        if name in self._system_data:
            return ObjectCategory.SYSTEM
        
        raise NameError(f"'{name}' is not a valid function, automaton or system.", name=name)

    def get_function_body(self, name: str) -> AttributedTree:
        if name in self._function_data:
            return self._function_data[name].copy()
        
        raise NameError(f"'{name}' is not a valid function.")

    def get_automaton_body(self, name: str) -> AttributedTree:
        if name in self._automaton_data:
            return self._automaton_data[name].copy()
        
        raise NameError(f"'{name}' is not a valid automaton.")

    def get_system_body(self, name: str) -> AttributedTree:
        if name in self._system_data:
            return self._system_data[name].copy()
        
        raise NameError(f"'{name}' is not a valid system.")

class ObjectTranslator(Translator):
    def __init__(self, type_context: TypeContext, actual_name: str, template_manager: TemplateManager, body: AttributedTree):
        super().__init__()
        self._type_context = type_context
        self._actual_name = actual_name
        self._template_manager = template_manager
        self._body = body
    
    def translate(self) -> Tuple[str, List[ExpansionRequest]]:
        #TODO
        pass

class LowLevelTranslator(ObjectTranslator):
    def __init__(self, type_context: TypeContext, actual_name: str,  template_manager: TemplateManager, body: AttributedTree):
        super().__init__(type_context, actual_name, template_manager, body)
    
    def _translate_var_decl(self, var_decl: AttributedTree) -> Tuple[str, List[ExpansionRequest]]:
        '''
        Warning: this method has side-effect (modifying type context)
        '''
        assert var_decl.name == "var_decl"
        
        init_resolved_term = InitTermTranslator(self._type_context, self._template_manager, var_decl.children[-1]).translate()
        init_term = init_resolved_term.python_code

        python_code = []

        #TODO
        for child in var_decl.children[:-1]:
            assert child.name == "IDENTIFIER"

            identifier = child.get_attribute("value")
            
            python_code.append("id_" + identifier + " = " + init_term + "\n")
        python_code = "".join(python_code)
        
        return python_code, init_resolved_term.expansion_requests

    def _translate_assign(self, assignment: AttributedTree) -> Tuple[str, List[ExpansionRequest]]:
        assert assignment.name == "assign_stmt"

        lhs_tree = assignment.get_child_by_name("lhs")
        rhs_tree = assignment.get_child_by_name("rhs")
        
        lhs_resolved_terms: List[ResolvedTerm] = []
        for term_tree in lhs_tree.children:
            lhs_resolved_terms.append(TermTranslator(self._type_context, self._template_manager, term_tree).translate())
        lhs_python_codes, lhs_type_trees, lhs_requests = ResolvedTerm.reshape(lhs_resolved_terms)

        rhs_resolved_terms: List[ResolvedTerm] = []
        for term_tree in rhs_tree.children:
            rhs_resolved_terms.append(TermTranslator(self._type_context, self._template_manager, term_tree).translate())
        rhs_python_codes, rhs_type_trees, rhs_requests = ResolvedTerm.reshape(lhs_resolved_terms)

        if lhs_tree.n_children == rhs_tree.n_children:
            for i in range(lhs_tree.n_children):
                rhs_python_codes[i] = rhs_type_trees[i].get_coercion(lhs_type_trees[i])(rhs_python_codes[i])

            python_code = ", ".join(lhs_python_codes) + ", = " + ", ".join(rhs_python_codes) + ",\n"
            return python_code, lhs_requests + rhs_requests
        
        if lhs_tree.n_children == 1:
            assert TypeTree.build_tuple_type(rhs_type_trees) <= lhs_type_trees[0]

            python_code = lhs_python_codes[0] + " = " + ", ".join(rhs_python_codes) + "\n"
            return python_code, lhs_requests + rhs_requests
        
        if rhs_tree.n_children == 1:
            assert TypeTree.build_array_type(lhs_type_trees) <= rhs_type_trees[0]

            python_code = ", ".join(lhs_python_codes) + " = " + rhs_python_codes[0]
            return python_code, lhs_requests + rhs_requests
        
        raise Exception("The LHS and RHS do not match.")        

    def translate(self) -> Tuple[str, List[ExpansionRequest]]:
        pass

class FunctionTranslator(LowLevelTranslator):
    def __init__(self, type_context: TypeContext, actual_name: str, template_manager: TemplateManager, body: AttributedTree):
        super().__init__(type_context, actual_name, template_manager, body)
        #TODO
    
    def _translate_return(self, return_stmt: AttributedTree) -> Tuple[str, List[ExpansionRequest]]:
        assert return_stmt.name == "return_stmt"

        term = return_stmt.children[0]

        resolved_term = TermTranslator(self._type_context, self._template_manager, term).translate()

        python_code = "return" + resolved_term.type_tree.get_coercion(self._type_context.get_param_type("!"))(resolved_term.python_code) + "\n"

        return python_code, resolved_term.expansion_requests

    def translate(self) -> Tuple[str, List[ExpansionRequest]]:
        python_codes = []
        all_requests = []
        for child in self._body.children:
            if child.name == "var_decl":
                python_code, requests = self._translate_var_decl(child)
            elif child.name == "assign_stmt":
                python_code, requests = self._translate_assign(child)
            elif child.name == "return_stmt":
                python_code, requests = self._translate_return(child)
            else:
                raise Exception
            
            python_codes.append(python_code)
            all_requests += requests
        
        function_body = indent_code("".join(python_codes), all_requests)
        function_code = "def" + self._actual_name + self._template_manager.get_signature_string(infer_original_name(self._actual_name)) + ":" + function_body

        return function_code, all_requests

class AutomatonTranslator(LowLevelTranslator):
    def __init__(self, type_context: TypeContext, actual_name: str, template_manager: TemplateManager, body: AttributedTree):
        super().__init__(type_context, actual_name, template_manager, body)
        #TODO
    
    def _translate_sync_stmt(self, sync_stmt: AttributedTree) -> str:
        assert sync_stmt.name == "sync_stmt"

        python_code = []
        for child in sync_stmt.children:
            identifier = child.get_attribute("value")

            _, IO = self._type_context.get_param_type(identifier, with_IO=True)
            
            python_code.append("await id_" + identifier + ".set(a)\n")
            python_code.append("await id_" + identifier + ".wait(a)\n")
            
        return "".join(python_code)

    def _translate_transition(self, transition: AttributedTree) -> Tuple[str, List[ExpansionRequest]]:
        if transition.name == "transition":
            return self._translate_single_guarded_stmt(transition.children[0])
        elif transition.name == "guarded_stmt_grp":
            return self._translate_guarded_stmt_grp(transition)
        else:
            raise Exception

    def _decompose_guarded_stmt(self, guarded_stmt: AttributedTree) -> Tuple[str, str, List[ExpansionRequest]]:
        assert guarded_stmt.name == "guarded_stmt"
        
        all_requests = []

        guard = guarded_stmt.children[0]
        guard_resolved = TermTranslator(self._type_context, self._template_manager, guard).translate()
        guard_python_code = guard_resolved.python_code
        all_requests += guard_resolved.expansion_requests

        stmt_code = []
        for stmt in guarded_stmt.children[1:]:
            if stmt.name == "assign_stmt":
                python_code, requests = self._translate_assign(stmt)
                stmt_code.append(python_code)
                all_requests += requests
            elif stmt.name == "sync_stmt":
                python_code = self._translate_sync_stmt(stmt)
                stmt_code.append(python_code)
            else:
                raise Exception
        stmt_code = "".join(stmt_code)

        return guard_python_code, stmt_code, all_requests

    def _translate_single_guarded_stmt(self, guarded_stmt: AttributedTree) -> Tuple[str, List[ExpansionRequest]]:
        guard_code, stmt_code, requests = self._decompose_guarded_stmt(guarded_stmt)
        
        python_code = "if " + guard_code + ":\n" + indent_code(stmt_code) + "\n"

        return python_code, requests

    def _translate_guarded_stmt_grp(self, guarded_stmt_grp: AttributedTree) -> Tuple[str, List[ExpansionRequest]]:
        assert guarded_stmt_grp.name == "guarded_stmt_grp"
        
        result_code = []

        all_requests = []
        guards = []
        stmt_codes = []

        for guarded_stmt in guarded_stmt_grp.children:
            guard_code, stmt_code, requests = self._decompose_guarded_stmt(guarded_stmt)
            guards.append(guard_code)
            stmt_codes.append(stmt_code)
            all_requests += requests

        guard_list_code = "g_lst = [" + ", ".join(guards) + "]\n"
        result_code.append(guard_list_code)
        result_code.append("choiced = random.choice(list([i for i in range(" + str(guarded_stmt_grp.n_children) + "if g_lst[i]]))\n")

        for i in range(guarded_stmt_grp.n_children):
            result_code.append("if choiced == " + str(i) + ": \n")
            result_code.append(indent_code(stmt_codes[i]))
            result_code.append("\n")
        
        return "".join(result_code), all_requests
    
    def translate(self) -> Tuple[str, List[ExpansionRequest]]:
        result_code = []
        all_requests = []

        automaton_vars = self._body.get_child_by_name("automaton_vars")

        for var_decl in automaton_vars.children:
            python_code, requests = self._translate_var_decl(var_decl)
            result_code.append(python_code)
            all_requests.append(requests)
            
        automaton_trans = self._body.get_child_by_name("automaton_trans")

        for transition in automaton_trans.children:
            python_code, requests = self._translate_transition(transition)
            result_code.append(python_code)
            all_requests.append(requests)

        result_code = "".join(result_code)

        result_code = "async def " + "run(self, " + self._template_manager.get_signature_string(infer_original_name(self._actual_name))[1:] + ":\n" + indent_code(result_code) + "\n"

        result_code = "class " + self._actual_name + ":\n" + indent_code(result_code)

        return result_code, all_requests

class SystemTranslator(ObjectTranslator):
    def __init__(self, type_context: TypeContext, actual_name: str, template_manager: TemplateManager ,body: AttributedTree):
        super().__init__(type_context, actual_name, template_manager, body)
        self.connections: Dict[str, ConnectionTable] = {}

    def _parse_components(self, system_comp: AttributedTree) -> List[ExpansionRequest]:
        assert system_comp.name == "system_comp"

        all_requests = []
        
        for component_decl in system_comp.children:
            all_requests += self._parse_component_decl(component_decl)
        
        return all_requests

    def _parse_component_decl(self, component_decl: AttributedTree) -> List[ExpansionRequest]:
        assert component_decl.name == "component_decl"

        entity_data = component_decl.children[-1]
        entity_name = entity_data.children[0].get_attribute("value")
        
        entity_tpl_apply = entity_data.get_child_by_name("template_apply", raise_exception=False)
        
        if entity_tpl_apply == None:
            entity_template_args = []
        else:
            entity_template_args = parse_template_apply(entity_tpl_apply)

        expansion_request = ExpansionRequest(entity_name, entity_template_args)
        
        expansion_datum = self._template_manager.query(expansion_request, raise_exception=False)

        requests = []

        if expansion_datum == None:
            expansion_datum = self._template_manager.create(expansion_request)
            requests.append(expansion_request)
        
        connection_table = expansion_datum.new_connection_table()

        for component in component_decl.children[:-1]:
            component_name = component.get_attribute("value")
            self.connections.update({component_name: connection_table.copy()})
        
        return requests
    
    def _parse_inter(self, inter: AttributedTree):
        assert inter.name == "system_inter"

        for node in inter.children:
            node_name = node.get_attribute("value")
            self._type_context.set_internal_node(node_name)
    
    def _parse_connections(self, system_conn: AttributedTree) -> Tuple[str, List[ExpansionRequest]]:
        assert system_conn.name == "system_conn"

        requests = []
        code_for_entities = []
        code_for_nodes = []
        all_node_names = []

        for connection_decl in system_conn.children:
            if connection_decl.name == "entity_connection":
                node_names = []

                connection_name = connection_decl.get_child_by_name("IDENTIFIER")
                
                connection_template_apply = connection_decl.get_child_by_name("template_apply", raise_exception=False)

                if connection_template_apply == None:
                    connection_template_args = []
                else:
                    connection_template_args = parse_template_apply(connection_template_apply)
                
                expansion_request = ExpansionRequest(connection_name, connection_template_args)

                expansion_datum = self._template_manager.query(expansion_request, raise_exception=False)

                if expansion_datum == None:
                    expansion_datum = self._template_manager.create(expansion_request)
                    requests.append(expansion_request)
                
                for port_name_tree in connection_decl.get_children_by_name("port_name"):
                    if port_name_tree.name == "comp_port_name":
                        comp_port_name = (port_name_tree.children[0].get_attribute("value"), port_name_tree.children[1].get_attribute("value"))
                        node_names.append(self._create_anonymous_node(comp_port_name))
                    elif port_name_tree.name == "sys_port_name":
                        port_name = port_name_tree.children[0].get_attribute("value")
                        node_names.append(port_name)
                
                code_for_entities.append("tg.create_task(" + expansion_datum.actual_name + "().run(" + ", ".join(node_names) + "))\n")
                
                all_node_names += node_names
            else:
                raise Exception
        
        for node_name in all_node_names:
            code_for_nodes.append(node_name + " = Node() \n")
        
        for component_name in self.connections:
            connection_table = self.connections[component_name]
            code_for_entities.append("tg.create_task(" + connection_table.translate() + ")\n")

        python_code = "".join(code_for_nodes) + "".join(code_for_entities)
        
        return python_code, requests

    def _create_anonymous_node(self, comp_port_name: Tuple[str, str]) -> str:
        #TODO
        pass

    def translate(self) -> Tuple[str, List[ExpansionRequest]]:
        all_requests = []
        
        system_comp = self._body.get_child_by_name("system_comp", raise_exception=False)
        system_inter = self._body.get_child_by_name("system_inter", raise_exception=False)
        system_conn = self._body.get_child_by_name("system_conn", raise_exception=False)
        
        all_requests += self._parse_components(system_comp)
        self._parse_inter(system_comp)

        code, requests = self._parse_connections(system_conn)
        all_requests += requests

        code = "async def " + self._actual_name + "(" + self._template_manager.get_signature_string(infer_original_name(self._actual_name)) + "): \n" + indent_code(code)
        
        return code, all_requests
    


class TermTranslator(Translator):
    def __init__(self, type_context: TypeContext, template_manager: TemplateManager, term_tree: AttributedTree):
        super().__init__()
        self._type_context = type_context
        self._template_manager = template_manager
        self._term_tree = term_tree
    
    def translate(self) -> "ResolvedTerm":
        DFS_manager = DFSManager(self._term_tree, self._translate)
        return DFS_manager.run()

    def _translate(self, current_tree: AttributedTree, children_resolved: "List[ResolvedTerm]") -> "ResolvedTerm":
        # Resolve info from children
        python_code_of_children: List[str] = []
        type_trees_of_children: List[TypeTree] = []
        requests_of_children: List[ExpansionRequest] = []
        for child_resolved in children_resolved:
            python_code_of_children.append(child_resolved.python_code)
            
            if child_resolved.type_tree == None and current_tree.name != "dot_term":
                raise Exception #TODO
            type_trees_of_children.append(child_resolved.type_tree)

            requests_of_children.append(child_resolved.expansion_requests)
        
        # Pure value
        if current_tree.name == "VALUE":
            value = current_tree.get_attribute("value")

            additional_info = ""

            if type(value) == int:
                return ResolvedTerm(f"MInt({value})", get_int_type(), [], additional_info=value)
            elif type(value) == float:
                return ResolvedTerm(f"MReal({value})", get_real_type(), [])
            elif type(value) == bool:
                return ResolvedTerm(f"MBool({value})", get_bool_type(), [])
            elif type(value) == str:
                return ResolvedTerm(f"MChar({value})", get_char_type(), [])
            else:
                raise Exception #TODO
        
        # Identifier (var/enum)
        if current_tree.name == "IDENTIFIER":
            identifier = current_tree.get_attribute("value")
            
            additional_info = ""

            if self._type_context.is_var(identifier): #var
                type_tree = self._type_context.type_of_var(identifier)
                python_code = "id_" + identifier
            
            if self._type_context.is_enum_type(identifier): #enum
                type_tree = None
                python_code = identifier
                additional_info = "enum"
            else:
                type_tree = None #TODO
                python_code = identifier
            
            return ResolvedTerm(python_code, type_tree, [], additional_info)
        
        if current_tree.name == "func_term":
            # Get function name
            function_name = current_tree.get_child_by_name("IDENTIFIER")
            
            # Get template info
            template_apply = current_tree.get_child_by_name("template_apply", raise_exception=False)
            
            if template_apply == None: # No template
                expansion_request = ExpansionRequest(function_name, [])
            else:
                template_args = parse_template_apply(template_apply)
                expansion_request = ExpansionRequest(function_name, template_args)
            
            # Try to get expansion datum (in order to get the signature)
            # If such datum does not exist, create it and add a new request to the request list.
            expansion_datum = self._template_manager.query(expansion_request, raise_exception=False)

            if expansion_datum == None:
                expansion_datum = self._template_manager.create(expansion_datum)
                requests_of_children.append(expansion_request)
            
            signature = expansion_datum.expanded_signature
            actual_name = expansion_datum.actual_name
            
            python_code = actual_name + signature.validate_and_convert(children_resolved)
            returned_type = signature.get_return_type()

            return ResolvedTerm(python_code, returned_type, requests_of_children)
        
        if current_tree.name == "struct_term":
            #TODO: normalize the tree
            python_code = []
            fields = current_tree.get_attribute("fields")
            type_tree = TypeTree.build_strcut_type(fields , type_trees_of_children)

            # Generate dictionary code
            for i in range(len(current_tree.n_children)):
                python_code.append(f"{fields[i]}: {python_code_of_children[i]}")
            python_code = r"{" + ", ".join(python_code) + r"}"
            
            return ResolvedTerm(python_code, type_tree, requests_of_children)

        if current_tree.name == "list_term":
            # Generate type
            type_tree = TypeTree.build_array_type(type_trees_of_children)

            # Generate python code
            python_code = r"[" + ", ".join(python_code_of_children) + r"]"
            
            return ResolvedTerm(python_code, type_tree, requests_of_children)
        
        if current_tree.name == "map_term":
            type_tree = TypeTree.build_map_type(type_trees_of_children)

            python_code = []
            for i in range(current_tree.n_children // 2):
                # Generate key code
                s11n_code = type_trees_of_children[2 * i].get_s11n_code()
                key_data = python_code_of_children[2 * i]
                key_code = f"pack({key_data}, {s11n_code})"

                # Generate value code
                value_code = python_code_of_children[2 * i + 1]
                
                # Generate key value pair code
                kv_code = f"{key_code}: {value_code}"
                python_code.append(kv_code)
            python_code = r"{" + ", ".join(python_code) + r"}"

            return ResolvedTerm(python_code, type_tree, requests_of_children)

        if current_tree.name == "dot_term":
            if children_resolved[0].additional_info == "enum":
                enum_alias = python_code_of_children[0]

                python_code = "enum_" + enum_alias + "." + python_code_of_children[1]
                
                type_tree = TypeTree.build_enum_type(enum_alias)
                
                return ResolvedTerm(python_code, type_tree, requests_of_children)
            
            if children_resolved[0].type_tree.name == "struct_type":
                field = python_code_of_children[1]

                python_code = r"("+ python_code_of_children[0] + r")" + "." + field
                
                type_tree = type_trees_of_children[0].get_child_by_name(field)
                
                return ResolvedTerm(python_code, type_tree, requests_of_children)

            port_name = children_resolved[0].python_code
            port_field = children_resolved[1].python_code
            if self._type_context.is_port(port_name):
                if port_field == "reqRead":
                    type_tree = get_bool_type()
                elif port_field == "reqWrite":
                    type_tree = get_bool_type()
                elif port_field == "value":
                    type_tree = self._type_context.get_param_type(port_name)
                else:
                    raise NameError(f"Ports do not have a field named'{port_name}'")
            
            raise Exception #TODO
        
        if current_tree.name == "brack_term":
            python_code = r"(" + python_code_of_children[0] + r")[" + python_code_of_children[1] + r"]"
            if type_trees_of_children[0] == "tuple_type":
                assert isinstance(children_resolved[1].additional_info, int)
                
                type_tree = type_trees_of_children[1].children[0].copy()
            elif type_trees_of_children[0] == "array_type" or type_trees_of_children[0] == "list_type":
                type_tree = type_trees_of_children[0].children[0].copy()
            elif type_trees_of_children[0] == "map_type":
                type_tree = type_trees_of_children[0].children[1].copy()
            else:
                raise Exception #TODO
            
            return ResolvedTerm(python_code, type_tree, requests_of_children)
        
        if current_tree.name == "tuple_term":
            type_tree = TypeTree.build_tuple_type(type_trees_of_children)

            python_code = []
            for tuple_component_code in python_code_of_children:
                python_code.append(tuple_component_code)
            python_code = r"(" + ", ".join(python_code) + r",)"

            return ResolvedTerm(python_code, type_tree, requests_of_children)            

class InitTermTranslator(Translator):
    def __init__(self, type_context: TypeContext, template_manager: TemplateManager, type_tree: TypeTree):
        super().__init__()
        self._type_context = type_context
        self._template_manager = template_manager
        self._type_tree = type_tree
    
    def translate(self) -> "ResolvedTerm":
        DFS_manager = DFSManager(self._type_tree, self._translate)
        return DFS_manager.run()
    
    def _translate(self, current_tree: TypeTree, children_returns: "List[ResolvedTerm]") -> "ResolvedTerm":
        requests = []
        python_code_from_children = []
        for resolved_term in children_returns:
            python_code_from_children.append(resolved_term.python_code)
            requests += resolved_term.expansion_requests
        
        if current_tree.name == "init_type":
            term_tree = current_tree.get_attribute("init_term")
            
            resolved_term = TermTranslator(self._type_context, self._template_manager, term_tree).translate()

            assert resolved_term.type_tree <= current_tree
            
            return resolved_term
        
        if current_tree.name == "array_type":            
            length = current_tree.get_attribute("length")
            python_code = r"[" + ', '.join([children_returns[0].python_code] * length) + r"]"
            
            return ResolvedTerm(python_code, None, requests)
        
        if current_tree.name == "struct_type":
            fields = current_tree.get_attribute("fields")
            
            python_code = []
            for i in range(current_tree.n_children):
                python_code.append(f"{fields[i]}: {children_returns[i].python_code}")
            python_code = r"{" + ", ".join(python_code) + r"}"
            
            return ResolvedTerm(python_code, None, requests)
        
        if current_tree.name == "tuple_type":
            python_code =  r"(" + ", ".join(python_code_from_children) + r",)"

            return ResolvedTerm(python_code, None, requests)
        
        return ResolvedTerm("None", None, requests)


class ResolvedTerm:
    def __init__(self, python_code: str, type_tree: TypeTree, expansion_requests: List[ExpansionRequest], additional_info: str = ""):
        self.python_code = python_code
        self.type_tree = type_tree
        self.expansion_requests = expansion_requests
        self.additional_info = additional_info

    @staticmethod
    def reshape(resolved_terms: "List[ResolvedTerm]") -> Tuple[List[str], List[TypeTree], List[ExpansionRequest]]:
        python_codes = []
        type_trees = []
        requests = []

        for resolved_term in resolved_terms:
            python_codes.append(resolved_term.python_code)
            type_trees.append(resolved_term.type_tree)
            requests += resolved_term.expansion_requests
        
        return python_codes, type_trees, requests