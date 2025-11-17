import uuid
import json
from datetime import datetime
from typing import List, Dict, Any, Union, Optional

# -----------------------------------------------
# ヘルパー & 基底クラス
# -----------------------------------------------

def generate_short_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"

class BaseEntity:
    """
    共通機能のみを提供する基底クラス。
    データの辞書化ロジック(to_dict)は各サブクラスに委譲する。
    """
    def as_json(self, indent: int = 2) -> str:
        """
        自身をJSON文字列に変換する。
        内部で各クラスの to_dict() を呼び出す。
        """
        def custom_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} is not JSON serializable")

        return json.dumps(
            self.to_dict(), 
            default=custom_serializer, 
            ensure_ascii=False, 
            indent=indent
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        【必須実装】自身のデータを辞書形式で返す。
        """
        raise NotImplementedError("Subclasses must implement to_dict()")


# -----------------------------------------------
# 4. Prologマッピング - 範囲定義 (Extent)
# -----------------------------------------------

class GeoExtentDescription(BaseEntity):
    def __init__(self, description: str):
        self.description = description

    def to_dict(self) -> Dict[str, Any]:
        return {
            "description": self.description
        }

class GeoExtentPoint(BaseEntity):
    def __init__(self, lat: float, lon: float):
        self.lat = lat
        self.lon = lon

    def to_dict(self) -> Dict[str, Any]:
        return {
            "lat": self.lat,
            "lon": self.lon
        }

class GeoExtentSurface(BaseEntity):
    def __init__(self, wkt: str):
        self.wkt = wkt
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "wkt": self.wkt
        }

# Type Hint
GeographicExtent = Union[GeoExtentDescription, GeoExtentPoint, GeoExtentSurface]


class TemporalExtentBetaDistribution(BaseEntity):
    def __init__(self, description: str, start_instant: datetime, end_instant: datetime, alpha: float, beta: float):
        self.description = description
        self.start_instant = start_instant
        self.end_instant = end_instant
        self.alpha = alpha
        self.beta = beta

    def to_dict(self) -> Dict[str, Any]:
        return {
            "description": self.description,
            "start_instant": self.start_instant, # JSON化時にas_json側でISO変換される
            "end_instant": self.end_instant,
            "alpha": self.alpha,
            "beta": self.beta
        }

class TemporalExtentInstant(BaseEntity):
    def __init__(self, instant: datetime):
        self.instant = instant

    def to_dict(self) -> Dict[str, Any]:
        return {
            "instant": self.instant
        }

# Type Hint
TemporalExtent = Union[TemporalExtentBetaDistribution, TemporalExtentInstant]


# -----------------------------------------------
# 5. Prologマッピング - CustomClass (階層型EAV)
# -----------------------------------------------

class Attribute(BaseEntity):
    def __init__(self, key: str, value: Any, datatype: str, description: str = "", id: Optional[str] = None, children: Optional[List['Attribute']] = None):
        self.id = id if id else generate_short_id("attr")
        self.key = key
        self.value = value
        self.datatype = datatype
        self.description = description
        self.children = children if children is not None else []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "key": self.key,
            "value": self.value,
            "datatype": self.datatype,
            "description": self.description,
            # 再帰的に子要素の to_dict を呼ぶ
            "children": [child.to_dict() for child in self.children]
        }

class CustomClass(BaseEntity):
    def __init__(self, classname: str, id: Optional[str] = None, attributes: Optional[List[Attribute]] = None, children: Optional[List['CustomClass']] = None):
        self.id = id if id else generate_short_id("cclass")
        self.classname = classname
        self.attributes = attributes if attributes is not None else []
        self.children = children if children is not None else []

    def add_attribute(self, attr: Attribute):
        self.attributes.append(attr)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "classname": self.classname,
            "attributes": [attr.to_dict() for attr in self.attributes],
            "children": [child.to_dict() for child in self.children]
        }


# -----------------------------------------------
# 3. Prologマッピング - 主要クラス
# -----------------------------------------------

class SourceMetadata(BaseEntity):
    def __init__(self, citation_id: str, reference_system_id: str, id: Optional[str] = None, additional_temporal_extent: Optional[Any] = None, additional_geographic_extent: Optional[Any] = None):
        self.id = id if id else generate_short_id("src")
        self.citation_id = citation_id
        self.reference_system_id = reference_system_id
        self.additional_temporal_extent = additional_temporal_extent
        self.additional_geographic_extent = additional_geographic_extent

    def to_dict(self) -> Dict[str, Any]:
        # additional_... が BaseEntity なら to_dict を呼ぶ、そうでなければそのまま
        ate = self.additional_temporal_extent
        age = self.additional_geographic_extent
        
        return {
            "id": self.id,
            "citation_id": self.citation_id,
            "reference_system_id": self.reference_system_id,
            "additional_temporal_extent": ate.to_dict() if isinstance(ate, BaseEntity) else ate,
            "additional_geographic_extent": age.to_dict() if isinstance(age, BaseEntity) else age
        }


class ContentsMetadata(BaseEntity):
    def __init__(self, 
                 abstract: str, 
                 topic_category: str, 
                 keyword_ids: List[str], 
                 geographic_extent: GeographicExtent, 
                 temporal_extent: TemporalExtent, 
                 id: Optional[str] = None,
                 custom_class_root: Optional[CustomClass] = None):
        
        self.id = id if id else generate_short_id("cont")
        self.abstract = abstract
        self.topic_category = topic_category
        self.keyword_ids = keyword_ids if keyword_ids is not None else []
        self.geographic_extent = geographic_extent
        self.temporal_extent = temporal_extent
        self.custom_class_root = custom_class_root

    def to_dict(self) -> Dict[str, Any]:
        # 1. 標準的なフィールドの辞書化
        data = {
            "id": self.id,
            "abstract": self.abstract,
            "topic_category": self.topic_category,
            "keyword_ids": self.keyword_ids,
            "geographic_extent": self.geographic_extent.to_dict() if self.geographic_extent else None,
            "temporal_extent": self.temporal_extent.to_dict() if self.temporal_extent else None,
        }

        # 2. custom_class_root の動的キー生成ロジック
        if self.custom_class_root:
            # キー名を "class: {classname}" にする
            key_name = f"class: {self.custom_class_root.classname}"
            data[key_name] = self.custom_class_root.to_dict()
        else:
            # データがない場合は None を明示するか、キーを含めないかは要件次第
            # ここではキーを含めない（スッキリさせる）実装にします
            pass

        return data

class Metadata(BaseEntity):
    """
    3.1. Metadata クラス (最上位コンテナ)
    修正: 複数の SourceMetadata と 複数の ContentsMetadata を保持できるように変更
    """
    def __init__(
            self, 
            contact_id: str,
            sources: Optional[List[SourceMetadata]] = None,   # 複数形に変更
            contents: Optional[List[ContentsMetadata]] = None, # 複数形に変更 (中身はリスト)
            id: Optional[str] = None, 
            language: str = "jpn", 
            datastamp: Optional[datetime] = None
    ):
        self.id = id if id else generate_short_id("meta")
        
        # リストの初期化 (Noneの場合は空リスト)
        self.sources = sources if sources is not None else []
        self.contents = contents if contents is not None else []
        
        self.contact_id = contact_id
        self.language = language
        self.datastamp = datastamp if datastamp else datetime.now()

    def add_source(self, source: SourceMetadata):
        """後からソースを追加するためのメソッド"""
        self.sources.append(source)

    def add_contents(self, content: ContentsMetadata):
        """後からコンテンツを追加するためのメソッド"""
        self.contents.append(content)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "datastamp": self.datastamp,
            "language": self.language,
            "contact_id": self.contact_id,
            # リスト内の各要素の to_dict を呼び出して展開する
            "sources": [src.to_dict() for src in self.sources],
            "contents": [cont.to_dict() for cont in self.contents]
        }