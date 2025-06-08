from typing import Any, Callable, Dict, List, Set, Tuple
import random
import asyncio

class Port:
    def __init__(self, s11n_code: Tuple = ("direct"), value: Any = None):
        self._value = value
        self.s11n_code = s11n_code
        self.reqRead: bool = False
        self.reqWrite: bool = False
        self._rendez_vous: Dict[int, asyncio.Event] = {}
    
    async def set(self, ID: int):
        if ID not in self._rendez_vous:
            self._rendez_vous.update({ID: asyncio.Event()})
        await self._rendez_vous[ID].set()
    
    async def wait(self, ID: int):
        for key in self._rendez_vous:
            if key != ID:
                return await self._rendez_vous[key].wait()
            
    @property
    def value(self):
        return unpack(pack(self.value, self._s11n_code))
    
    @value.setter
    def value(self, val):
        self._value = val

class MUnion:
    def __init__(self, label: int, value: Any):
        self.label = label
        self.value = value

def pack(data: Any, s11n_code: Tuple) -> Any:
    mode = s11n_code[0]

    if mode == "direct":
        return ("direct", data)
    
    if mode == "bounded":
        _, l, r = s11n_code
        
        # assert bound
        if not (l <= data and data <= r):
            raise ValueError(f"Value {data} is not an integer between {l} and {r}")
        
        return ("direct", data)
    
    if mode == "tuple":
        assert len(data) + 1 == len(s11n_code)

        result = []
        for i in range(1, len(s11n_code)):
            result.append(pack(data[i - 1], s11n_code[i]))
        
        return tuple(["tuple"] + result)
    
    if mode == "union":
        assert isinstance(data, MUnion)
        
        label = data.label
        
        return pack(data.value, s11n_code[label + 1])
    
    if mode == "array":
        assert len(data) <= s11n_code[1]
        
        result = []
        for i in range(len(data)):
            result.append(pack(data[i], s11n_code[2]))
        
        # padding
        for i in range(s11n_code[1] - len(data)):
            result.append(None)
        
        return tuple(["list"] + result)
    
    if mode == "list":
        result = []
        for i in range(len(data)):
            result.append(pack(data[i], s11n_code[1]))
        
        return tuple(["list"] + result)
    
    if mode == "map":
        _, key_s11n_code, value_s11n_code = s11n_code
        
        result = []
        for key in data:
            key_packed = pack(unpack(key), key_s11n_code)
            value_packed = pack(data[key], value_s11n_code)
            result.append((key_packed, value_packed))
        
        return tuple(["map"] + result)
    
    if mode == "struct":
        result = []
        for i in range(1, len(s11n_code)):
            field, field_s11n_code = mode
            result.append((field, pack(data[field], field_s11n_code)))
        
        return tuple(["struct"] + result)
    
    if mode == "inj":
        return ("union", s11n_code[1], pack(data, s11n_code[2]))
    
    raise ValueError(f"Invalid serialization code '{s11n_code}'")

def unpack(s11n: Tuple) -> Any:
    mode = s11n[0]

    if mode == "direct":
        return s11n[1]
    
    if mode == "tuple":
        result = []
        for i in range(1, len(s11n)):
            result.append(unpack(s11n[i]))
        
        return result
    
    if mode == "union":
        return MUnion(s11n[1], unpack(s11n[2]))
    
    if mode == "list":
        result = []
        for i in range(1, len(s11n)):
            result.append(unpack(s11n[i]))
        
        return result
    
    if mode == "map":
        result = {}
        for i in range(1, len(s11n)):
            key, value = s11n[i][0], unpack(s11n[i][1])
            if key in result:
                print(f"Warning: Duplicated map key '{key}' when deserializing.")
            
            result.update({key: value})

        return result
    
    if mode == "struct":
        result = {}
        for i in range(1, len(s11n)):
            key, value = s11n[i][0], unpack(s11n[i][1])
            result.update({key: value})
        
        return result
    
    raise ValueError("Invalid serialization data!")

def convert(data: Any, s11n_code: str) -> Any:
    return unpack(pack(data, s11n_code))
