import uuid
import json
from datetime import datetime
from typing import List, Dict, Any, Union, Optional

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
        raise NotImplementedError("Subclasses must implement to_dict()")
    
    def to_searchable_metadata(self) -> Dict[str, Union[str, int, float, bool]]:
        flat_dict = {}
        original_dict = self.to_dict()
        
        for key, value in original_dict.items():
            if isinstance(value, (str, int, float, bool)) and value is not None:
                flat_dict[key] = value
            elif value is None:
                flat_dict[key] = "" 
            else:
                flat_dict[key] = json.dumps(value, default=str, ensure_ascii=False)
        
        return flat_dict

class GeoExtentString(BaseEntity):
    """地名などの文字情報"""
    def __init__(self, place_name: str, description: str):
        self.place_name = place_name
        self.description = description

    def to_dict(self) -> Dict[str, Any]:
        return {
            "place_name": self.place_name,
            "description": self.description
        }

class GeoExtentPoint(BaseEntity):
    """点情報 (緯度経度)"""
    def __init__(self, lat: float, lon: float):
        self.lat = lat
        self.lon = lon

    def to_dict(self) -> Dict[str, Any]:
        return {
            "lat": self.lat,
            "lon": self.lon,
            # 必要ならここで自動的にWKTを生成して保持しても良い
            "wkt": f"POINT({self.lon} {self.lat})" 
        }

class GeoExtentBoundingbox(BaseEntity):
    """
    矩形範囲 (Bounding Box)
    修正: 文字列ではなく float で持ち、辞書キーも box 用にする
    """
    def __init__(self, north: float, west: float, south: float, east: float):
        self.north = north
        self.west = west
        self.south = south
        self.east = east

    def to_dict(self) -> Dict[str, Any]:
        return {
            "north": self.north,
            "west": self.west,
            "south": self.south,
            "east": self.east,
            # WKT (POLYGON) 表記の生成
            "wkt": f"POLYGON(({self.west} {self.north}, {self.east} {self.north}, {self.east} {self.south}, {self.west} {self.south}, {self.west} {self.north}))"
        }

class GeoExtentSurface(BaseEntity):
    """複雑な形状 (WKTそのもの)"""
    def __init__(self, wkt: str):
        self.wkt = wkt
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "wkt": self.wkt
        }

# 型定義
GeographicExtent = Union[
    GeoExtentString, 
    GeoExtentPoint, 
    GeoExtentSurface,
    GeoExtentBoundingbox
]

class TemporalExtentBetaDistribution(BaseEntity):
    def __init__(self, description: str, start_instant: datetime, expected_instant: datetime, end_instant: datetime, alpha: float, beta: float):
        self.description = description
        self.start_instant = start_instant
        self.expected_instant = expected_instant
        self.end_instant = end_instant
        self.alpha = alpha
        self.beta = beta

    def to_dict(self) -> Dict[str, Any]:
        return {
            "description": self.description,
            "start_instant": self.start_instant, 
            "expected_instant": self.expected_instant,
            "end_instant": self.end_instant,
            "alpha": self.alpha,
            "beta": self.beta
        }

class TemporalExtentPeriod(BaseEntity):
    def __init__(self, date_from: datetime, date_expected: datetime, date_to: datetime, description: str):
        self.description = description
        # 修正: to_dict と合わせるために変数名を変更
        self.date_from = date_from
        self.date_expected = date_expected
        self.date_to = date_to

    def to_dict(self) -> Dict[str, Any]:
        return {
            "date_from": self.date_from, 
            "date_expected": self.date_expected,
            "date_to": self.date_to,
            "description": self.description
        }

class TemporalExtentString(BaseEntity):
    def __init__(self, date_from: str, date_expected: str, date_to: str, description: str):
        self.description = description
        self.date_from = date_from
        self.date_expected = date_expected
        self.date_to = date_to

    def to_dict(self) -> Dict[str, Any]:
        return {
            "date_from": self.date_from, 
            "date_expected": self.date_expected,
            "date_to": self.date_to,
            "description": self.description
        }

class TemporalExtentNumber(BaseEntity):
    def __init__(self, date_from: float, date_expected: float, date_to: float, description: str):
        self.description = description
        self.date_from = date_from
        self.date_expected = date_expected
        self.date_to = date_to

    def to_dict(self) -> Dict[str, Any]:
        return {
            "date_from": self.date_from, 
            "date_expected": self.date_expected,
            "date_to": self.date_to,
            "description": self.description
        }

# Union型の更新
TemporalExtent = Union[
    TemporalExtentBetaDistribution, 
    TemporalExtentPeriod, 
    TemporalExtentString,
    TemporalExtentNumber
]

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

class SourceMetadata(BaseEntity):
    def __init__(self, citation_id: str, reference_system_id: str, id: Optional[str] = None, additional_temporal_extent: Optional[Any] = None, additional_geographic_extent: Optional[Any] = None):
        self.id = id if id else generate_short_id("src")
        self.citation_id = citation_id
        self.reference_system_id = reference_system_id
        self.additional_temporal_extent = additional_temporal_extent
        self.additional_geographic_extent = additional_geographic_extent

    def to_dict(self) -> Dict[str, Any]:
        ate = self.additional_temporal_extent
        age = self.additional_geographic_extent
        
        return {
            "id": self.id,
            "citation_id": self.citation_id,
            "reference_system_id": self.reference_system_id,
            "additional_temporal_extent": ate.to_dict() if isinstance(ate, BaseEntity) else ate,
            "additional_geographic_extent": age.to_dict() if isinstance(age, BaseEntity) else age
        }
    
    def to_collection_metadata(self) -> Dict[str, Any]:
        # 基本情報
        meta = {
            "source_id": self.id,
            "citation_id": self.citation_id,
            "reference_system": self.reference_system_id,
            "structured": self.as_json(indent=None)
        }

        # 地理的範囲の展開 (src_geo_ プレフィックス)
        if self.additional_geographic_extent:
            ge = self.additional_geographic_extent
            
            if isinstance(ge, GeoExtentString):
                meta["src_geo_type"] = "string"
                meta["src_geo_place"] = ge.place_name
            
            elif isinstance(ge, GeoExtentPoint):
                meta["src_geo_type"] = "point"
                meta["src_geo_lat"] = float(ge.lat)
                meta["src_geo_lon"] = float(ge.lon)
            
            elif isinstance(ge, GeoExtentBoundingbox):
                meta["src_geo_type"] = "bbox"
                meta["src_geo_north"] = float(ge.north)
                meta["src_geo_west"] = float(ge.west)
                meta["src_geo_south"] = float(ge.south)
                meta["src_geo_east"] = float(ge.east)

            elif isinstance(ge, GeoExtentSurface):
                meta["src_geo_type"] = "surface"
                # WKT文字列として保存
                meta["src_geo_wkt"] = str(ge.wkt)

        # 時間的範囲の展開 (src_temp_ プレフィックス)
        if self.additional_temporal_extent:
            te = self.additional_temporal_extent
            
            if isinstance(te, TemporalExtentPeriod):
                meta["temp_type"] = "period"
                meta["temp_period_from"] = te.date_from.timestamp()
                meta["temp_period_expected"] = te.date_expected.timestamp()
                meta["temp_period_to"] = te.date_to.timestamp()

            elif isinstance(te, TemporalExtentString):
                meta["src_temp_type"] = "string"
                meta["src_temp_str_from"] = te.date_from
                meta["src_temp_str_expected"] = te.date_expected
                meta["src_temp_str_to"] = te.date_to

            elif isinstance(te, TemporalExtentNumber):
                meta["src_temp_type"] = "number"
                meta["src_temp_num_from"] = float(te.date_from)
                meta["src_temp_num_expected"] = float(te.date_expected)
                meta["src_temp_num_to"] = float(te.date_to)

            elif isinstance(te, TemporalExtentBetaDistribution):
                meta["src_temp_type"] = "distribution"
                meta["src_temp_start"] = te.start_instant.isoformat()
                meta["src_temp_expected"] = te.expected_instant.isoformat()
                meta["src_temp_end"] = te.end_instant.isoformat()

        return meta

class ContentsMetadata(BaseEntity):
    def __init__(self, 
                 title: str,
                 reference: str,
                 abstract: str, 
                 topic_category: str, 
                 keyword_ids: List[str], 
                 geographic_extent: GeographicExtent, 
                 temporal_extent: TemporalExtent, 
                 id: Optional[str] = None,
                 custom_class_root: Optional[CustomClass] = None):
        
        self.id = id if id else generate_short_id("cont")
        self.title = title
        self.reference = reference
        self.abstract = abstract
        self.topic_category = topic_category
        self.keyword_ids = keyword_ids if keyword_ids is not None else []
        self.geographic_extent = geographic_extent
        self.temporal_extent = temporal_extent
        self.custom_class_root = custom_class_root

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "id": self.id,
            "title": self.title,
            "reference": self.reference,
            "abstract": self.abstract,
            "topic_category": self.topic_category,
            "keyword_ids": self.keyword_ids,
            "geographic_extent": self.geographic_extent.to_dict() if self.geographic_extent else None,
            "temporal_extent": self.temporal_extent.to_dict() if self.temporal_extent else None,
        }
        if self.custom_class_root:
            key_name = f"class: {self.custom_class_root.classname}"
            data[key_name] = self.custom_class_root.to_dict()
        return data
    
    def to_searchable_metadata(self) -> Dict[str, Any]:
        # 基本フィールド
        flat_meta = {
            "id": self.id,
            "reference": self.reference,
            "abstract": self.abstract,
            "topic_category": self.topic_category,
            "keywords_str": ",".join(self.keyword_ids), 
            "structured": self.as_json(indent=None)
        }

        # 地理フィールド
        if self.geographic_extent:
            ge = self.geographic_extent
            
            ge_dict = ge.to_dict()
            if "wkt" in ge_dict:
                flat_meta["geo_wkt"] = ge_dict["wkt"]

            if isinstance(ge, GeoExtentString):
                flat_meta["geo_type"] = "string"
                flat_meta["geo_place"] = ge.place_name

            elif isinstance(ge, GeoExtentPoint):
                flat_meta["geo_type"] = "point"
                flat_meta["geo_lat"] = float(ge.lat)
                flat_meta["geo_lon"] = float(ge.lon)
            
            elif isinstance(ge, GeoExtentBoundingbox):
                flat_meta["geo_type"] = "bbox"
                flat_meta["geo_north"] = float(ge.north)
                flat_meta["geo_west"] = float(ge.west)
                flat_meta["geo_south"] = float(ge.south)
                flat_meta["geo_east"] = float(ge.east)

            elif isinstance(ge, GeoExtentSurface):
                flat_meta["geo_type"] = "surface"

        # 3. 時間的範囲 (TemporalExtent) の展開
        if self.temporal_extent:
            te = self.temporal_extent
            
            # 共通の説明フィールドがあれば入れる
            if hasattr(te, 'description') and te.description:
                flat_meta["temp_desc"] = te.description

            # --- A. Period (datetime型: 日付範囲検索用) ---
            if isinstance(te, TemporalExtentPeriod):
                flat_meta["temp_type"] = "period"
                flat_meta["temp_period_from"] = te.date_from.timestamp()
                flat_meta["temp_period_expected"] = te.date_expected.timestamp()
                flat_meta["temp_period_to"] = te.date_to.timestamp()

            # --- B. String (文字列型: "江戸時代"などのキーワード検索用) ---
            elif isinstance(te, TemporalExtentString):
                flat_meta["temp_type"] = "string"
                flat_meta["temp_str_from"] = te.date_from
                flat_meta["temp_str_expected"] = te.date_expected
                flat_meta["temp_str_to"] = te.date_to

            # --- C. Number (数値型: 西暦年や世紀などの数値範囲検索用) ---
            elif isinstance(te, TemporalExtentNumber):
                flat_meta["temp_type"] = "number"
                # float型として保存 ($gt, $lt などで検索可能)
                flat_meta["temp_num_from"] = float(te.date_from)
                flat_meta["temp_num_expected"] = float(te.date_expected)
                flat_meta["temp_num_to"] = float(te.date_to)

            # --- D. BetaDistribution (確率モデル: 高度な分析用) ---
            elif isinstance(te, TemporalExtentBetaDistribution):
                flat_meta["temp_type"] = "distribution"
                flat_meta["temp_dist_start"] = te.start_instant.isoformat()
                flat_meta["temp_dist_expected"] = te.expected_instant.isoformat()
                flat_meta["temp_dist_end"] = te.end_instant.isoformat()
                flat_meta["temp_dist_alpha"] = float(te.alpha)
                flat_meta["temp_dist_beta"] = float(te.beta)
        
        # カスタムクラス（階層構造）の展開
        if self.custom_class_root:
            self._flatten_custom_class_recursive(self.custom_class_root, flat_meta, [])

        return flat_meta

    def _flatten_custom_class_recursive(
            self, 
            c_class: CustomClass, 
            target_dict: Dict[str, Any], 
            path_stack: List[str]
        ):
        
        # 現在のクラス名をパスに追加
        current_path = path_stack + [c_class.classname]
        
        # パスを文字列化する (区切り文字は検索しやすいものを選ぶ)
        path_key_prefix = "/".join(current_path)

        # 自身の属性 (Attribute) を展開
        for attr in c_class.attributes:
            # 完全なユニークキーを作成
            full_key = f"{path_key_prefix}/{attr.key}"
            
            # 値の型チェックと格納
            if isinstance(attr.value, (str, int, float, bool)):
                target_dict[full_key] = attr.value
            else:
                target_dict[full_key] = str(attr.value)

        # 子クラス (Children) があれば再帰的に処理
        for child in c_class.children:
            self._flatten_custom_class_recursive(child, target_dict, current_path)

class Metadata(BaseEntity):
    def __init__(
            self, 
            contact_id: str,
            sources: Optional[List[SourceMetadata]] = None,  
            contents: Optional[List[ContentsMetadata]] = None, 
            id: Optional[str] = None, 
            language: str = "jpn", 
            datastamp: Optional[datetime] = None
    ):
        self.id = id if id else generate_short_id("meta")
        self.sources = sources if sources is not None else []
        self.contents = contents if contents is not None else []        
        self.contact_id = contact_id
        self.language = language
        self.datastamp = datastamp if datastamp else datetime.now()

    def add_source(self, source: SourceMetadata):
        self.sources.append(source)

    def add_contents(self, content: ContentsMetadata):
        self.contents.append(content)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "datastamp": self.datastamp,
            "language": self.language,
            "contact_id": self.contact_id,
            "sources": [src.to_dict() for src in self.sources],
            "contents": [cont.to_dict() for cont in self.contents]
        }