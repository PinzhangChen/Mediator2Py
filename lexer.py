import re
import os
from enum import Enum
from typing import List, Tuple, Dict, Any

class LexerMode(Enum):
    NO = 0
    SINGLELINE_COMMENT = 1
    MULTILINE_COMMENT = 2
    CHARACTER = 3
    IDENTIFIER = 4
    NUMBER = 5

KEYWORDS = {"import": "Import", "typedef": "Tdef", "as": "As", "int": "Int", "..": "Ddot", "real": "Real", "bool": "Bool", "char": "Char", "enum": "Enum", "type": "Abstype", "tuple": "Tuple", "map": "Map", "struct": "Struct", "init": "Init", "interface": "Interface", "in": "In", "out": "Out", "func": "Functype", "automaton": "Auto", "variables": "Vars", "function": "Func", "statements": "Stmts", "return": "Return", "transitions": "Trans", "group": "Grp", "sync": "Sync", "async": "Async", "system": "Sys", "internals": "Inter", "components": "Comp", "connections": "Conn", "(": "Lparen", ")": "Rparen", "{": "Lbrace", "}": "Rbrace", "[": "Lbrack", "]": "Rbrack", ",": "Comma", ";": "Semicolon", "+": "Plus", "*": "Mul", "%": "Mod"}
# Any keyword can ONLY contain Latin letters.
# The initial letters MUST be capitalized.
# The rest part MUST be lowercased.


def tokenize(code: str) -> List[Dict[str, Any]]:
    '''TODO
    '''
    
    # Preprocess
    lexemes = re.sub(r"\r\n|\r|\n", "\n", code)
    lexemes = list(lexemes)
    lexemes.append("\x00") # sentinel

    try:
        tokens = []

        i = 0
        line = 1
        col = 0

        mode = LexerMode.NO
        lexeme_line = 1
        lexeme_col = 0
        met_dot = False
        symbol_stack = []
        
        while True:
            cur_symbol = lexemes[i]
            col += 1

            # Linesep
            if cur_symbol == "\n":
                line += 1
                col = 0
                
                if mode == LexerMode.SINGLELINE_COMMENT:
                    mode = LexerMode.NO
                
                i += 1
                continue
            
            # Each mode other than NO
            if mode == LexerMode.SINGLELINE_COMMENT:
                i += 1
                continue
            elif mode == LexerMode.MULTILINE_COMMENT:
                if cur_symbol == "*" and lexemes[i + 1] == "/": # IndexError
                    mode = LexerMode.NO
                    i += 2
                    col += 1
                    continue

                i += 1
                continue
            elif mode == LexerMode.CHARACTER:
                # Exit char mode
                if cur_symbol == "'" and symbol_stack != ["\\"]:
                    # Create new token
                    char = ''.join(symbol_stack)
                    symbol_stack = []
                    char = char.encode("utf-8").decode("unicode_escape")
                    if len(char) != 1:
                        raise SyntaxError(f"[line {lexeme_line}, col {lexeme_col}] Too many characters for char type: expected 1, received {len(char)}")
                    tokens.append({"token": "value", "value": char, "line": lexeme_line, "col": lexeme_col})
                    
                    # Reset the mode
                    mode = LexerMode.NO

                    # Next
                    i += 1
                    continue
                
                symbol_stack.append(cur_symbol)
            elif mode == LexerMode.IDENTIFIER:
                if re.match(r"\w", cur_symbol) == None:
                    # Pop the symbol stack
                    identifier = ''.join(symbol_stack)
                    symbol_stack = []
                    
                    # Create token
                    if identifier in KEYWORDS:
                        tokens.append({"token": KEYWORDS[identifier], "value": None, "line": lexeme_line, "col": lexeme_col})
                    elif identifier == "true" or identifier == "false":
                        tokens.append({"token": "value", "value": bool(identifier), "line": lexeme_line, "col": lexeme_col})
                    else:
                        tokens.append({"token": "identifier", "value": identifier, "line": lexeme_line, "col": lexeme_col})
                    
                    # Reset the mode
                    mode = LexerMode.NO

                    # Adress current symbol
                    continue 
                
                symbol_stack.append(cur_symbol)
                i += 1
                continue
            elif mode == LexerMode.NUMBER:
                if re.match(r"\d", cur_symbol):
                    symbol_stack.append(cur_symbol)
                    
                    i += 1
                    continue
                
                if cur_symbol == "." and not met_dot:
                    if lexemes[i + 1] == ".":
                        num = int(''.join(symbol_stack))
                        symbol_stack = []
                        
                        tokens.append({"token": "value", "value": num, "line": lexeme_line, "col": lexeme_col})
                        
                        tokens.append({"token": "Ddot", "value": None, "line": line, "col": col})

                        mode = LexerMode.NO

                        i += 2
                        col += 1
                        continue
                    
                    if re.match(r"\d", lexemes[i + 1]):
                        symbol_stack.append(".")
                        met_dot = True
                        i += 1
                        continue

                    raise SyntaxError(f"[line {line}, col {col}] Extra dot.")
                
                tar_type = float if met_dot else int
                num = tar_type(''.join(symbol_stack))
                symbol_stack = []
                met_dot = False

                tokens.append({"token": "value", "value": num, "line": lexeme_line, "col": lexeme_col})
                
                mode = LexerMode.NO

                continue
            
            # Safe punctuations
            if cur_symbol in KEYWORDS:
                tokens.append({"token": KEYWORDS[cur_symbol], "value": None, "line": line, "col": col})

                i += 1
                continue
            
            # . or ..
            if cur_symbol == ".":
                next_symbol = lexemes[i + 1]
                if next_symbol == ".":
                    token = "Ddot"
                    i += 1
                    col += 1
                else:
                    token = "Dot"
                    i += 1
                    col += 1
                
                tokens.append({"token": token, "value": None, "line": line, "col": col})

                i += 1
                continue
            
            # = or == or =>
            if cur_symbol == "=":
                next_symbol = lexemes[i + 1]
                if next_symbol == "=":
                    token = "Eq"
                    i += 1
                    col += 1
                elif next_symbol == ">":
                    token = "Mapsto"
                    i += 1
                    col += 1
                else:
                    token = "Assgt"
                
                tokens.append({"token": token, "value": None, "line": line, "col": col})

                i += 1
                continue
            
            # - or ->
            if cur_symbol == "-":
                next_symbol = lexemes[i + 1]
                if next_symbol == ">":
                    token = "Transto"
                    i += 1
                    col += 1
                else:
                    token = "Min"
                
                tokens.append({"token": token, "value": None, "line": line, "col": col})

                i += 1
                continue
            
            # > or >= 
            if cur_symbol == ">":
                next_symbol = lexemes[i + 1]
                if next_symbol == "=":
                    token = "Geq"
                    i += 1
                    col += 1
                else:
                    token = "Gt"
                
                tokens.append({"token": token, "value": None, "line": line, "col": col})
                
                i += 1
                continue

            # < or <= 
            if cur_symbol == "<":
                next_symbol = lexemes[i + 1]
                if next_symbol == "=":
                    token = "Leq"
                    i += 1
                    col += 1
                else:
                    token = "Lt"
                
                tokens.append({"token": token, "value": None, "line": line, "col": col})

                i += 1
                continue

            # / or // or /* 
            if cur_symbol == "/":
                next_symbol = lexemes[i + 1]
                if next_symbol == "/":
                    mode = LexerMode.SINGLELINE_COMMENT
                elif next_symbol == "*":
                    mode = LexerMode.MULTILINE_COMMENT
                else:
                    tokens.append({"token": "Div", "value": None, "line": line, "col": col})
                
                i += 1
                continue

            # | or ||
            if cur_symbol == "|":
                next_symbol = lexemes[i + 1]
                if next_symbol == "|":
                    token = "Or"
                    i += 1
                    col += 1
                else:
                    token = "Mid"
                
                tokens.append({"token": token, "value": None, "line": line, "col": col})

                i += 1
                continue

            # ! and !=
            if cur_symbol == "!":
                next_symbol = lexemes[i + 1]
                if next_symbol == "=":
                    i += 1
                    col += 1
                    token = "Neq"
                else:
                    token = "Not"
                
                tokens.append({"token": token, "value": None, "line": line, "col": col})
                
                i += 1
                continue

            # && 
            if cur_symbol == "&":
                next_symbol = lexemes[i + 1]
                if next_symbol != "&":
                    raise SyntaxError(f"[line {line}, col {col}] Missing &.")
                i += 2
                col += 1

                tokens.append({"token": "And", "value": None, "line": line, "col": col})
                continue

            # : and ::
            if cur_symbol == ":":
                next_symbol = lexemes[i + 1]
                if next_symbol == ":":
                    i += 1
                    col += 1
                    token = "Scope"
                else:
                    token = "Colon"
                
                tokens.append({"token": token, "value": None, "line": line, "col": col})
                
                i += 1
                continue


            # char mode
            if cur_symbol == "'":
                mode = LexerMode.CHARACTER
                lexeme_line = line
                lexeme_col = col + 1
                i += 1
                continue

            # identifier mode
            if re.match(r"\d", cur_symbol) == None and re.match(r"\w", cur_symbol):
                mode = LexerMode.IDENTIFIER
                lexeme_line = line
                lexeme_col = col
                symbol_stack.append(cur_symbol)
                i += 1
                continue
            
            # number mode
            if re.match(r"\d", cur_symbol):
                mode = LexerMode.NUMBER
                lexeme_line = line
                lexeme_col = col
                symbol_stack.append(cur_symbol)
                i += 1
                continue

            # sentinel
            if cur_symbol == "\x00":
                break

            # invalid character
            if re.match(r"\s", cur_symbol) == None:
                raise SyntaxError(f"[line {line}, col {col}] Invalid character {cur_symbol}")
            
            i += 1
    except IndexError:
        if mode == LexerMode.MULTILINE_COMMENT:
            raise SyntaxError(f"[line {lexeme_line}, col {lexeme_col}] Unclosed multiline comments")
        else:
            raise Exception("Unknown index error when tokenizing.")
    
    return tokens

def post_process(tokens : List[Dict[str, Any]]) -> str:
    '''
    TODO
    '''
    result = []

    for i in range(len(tokens)):
        token = tokens[i]
        token_name = token["token"]

        if token_name == "identifier":
            result.append(f"Id@{i}")
        elif token_name == "value":
            result.append(f"Val@{i}")
        else:
            result.append(token_name)
        
    return ' '.join(result)
