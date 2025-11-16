import inspect
from abc import ABC 
from types import SimpleNamespace
from typing import List, Any, NamedTuple

from .additional_attribute import AddtionalAttribute

class AbstractCustomClass(ABC):
    def define_custom_table():
        pass
    def create_table(self):
        pass

class CustomClassGenerator:
    def __init__(
        self,
        classname: str = None,
        attributes: List[AddtionalAttribute] = None
    ):
        self.classname = classname
        self.instance = self._setCustomObject(attributes)
    
    def _setCustomObject(self, attributes: List[AddtionalAttribute]) -> object:
        custom_object = SimpleNamespace()
        for attr in attributes:
            if not isinstance(attr.key, str) or not attr.key: continue
            target_object = custom_object
            try:
                if attr.namespace:
                    if not hasattr(target_object, attr.namespace):
                        setattr(target_object, attr.namespace, SimpleNamespace())
                    target_object = getattr(target_object, attr.namespace)
                if attr.classname:
                    if not hasattr(target_object, attr.classname):
                        setattr(target_object, attr.classname, SimpleNamespace())
                    target_object = getattr(target_object, attr.classname)
                value_to_set = self._convert_value_by_type(attr.value, attr.datatype)
                setattr(target_object, attr.key, value_to_set)
            except (AttributeError, ValueError) as e:
                print(f"エラー: 属性 '{attr.key}' の設定または変換に失敗しました。理由: {e}")
        return custom_object

    def _convert_value_by_type(self, value: Any, datatype: str) -> Any:
        if not datatype: return value
        datatype = datatype.lower()
        try:
            if datatype == "int": return int(value)
            elif datatype == "float": return float(value)
            elif datatype == "bool":
                if isinstance(value, str):
                    return value.lower() in ("true", "1", "yes", "t")
                return bool(value)
            elif datatype == "str": return str(value)
            else: return value
        except (ValueError, TypeError): return value

    def __repr__(self) -> str:
        if self.instance:
            return f"CustomClassGenerator(instance={self._repr_simple_namespace(self.instance)})"
        return "CustomClassGenerator(instance=None)"

    def _repr_simple_namespace(self, obj: Any) -> str:
        if isinstance(obj, SimpleNamespace):
            try:
                items = {k: self._repr_simple_namespace(v) for k, v in obj.__dict__.items()}
                return f"{items}"
            except RecursionError: return "[RecursionError]"
        elif isinstance(obj, list):
            return f"[{', '.join(self._repr_simple_namespace(i) for i in obj)}]"
        else: return repr(obj)

    def get_class(self, instance: SimpleNamespace, root_class_name: str = "RootClass") -> type:        
        if not isinstance(instance, SimpleNamespace):
            raise TypeError("入力は SimpleNamespace インスタンスである必要があります。")

        class_attributes = {}
        init_definitions = {}

        for key, value in instance.__dict__.items():
            if isinstance(value, SimpleNamespace):
                # ネストされたクラスも再帰的に get_class で定義する
                nested_class_name = key[0].upper() + key[1:] + "Class"
                NestedClass = self.get_class(value, nested_class_name)
                
                class_attributes[nested_class_name] = NestedClass
                init_definitions[key] = NestedClass
                
            else:
                init_definitions[key] = value

        # __init__ メソッドを動的に定義
        def __init__(self):
            for attr_name, val_or_type in init_definitions.items():
                if inspect.isclass(val_or_type):
                    setattr(self, attr_name, val_or_type())
                else:
                    setattr(self, attr_name, val_or_type)

        class_attributes['__init__'] = __init__

        # __repr__ メソッドも定義
        def __repr__(self):
            attrs_list = []
            for key in init_definitions.keys():
                if hasattr(self, key):
                    attrs_list.append(f"{key}={getattr(self, key)!r}")
            return f"{root_class_name}({', '.join(attrs_list)})"

        class_attributes['__repr__'] = __repr__

        NewClass = type(root_class_name, (AbstractCustomClass,), class_attributes)
        
        return NewClass
