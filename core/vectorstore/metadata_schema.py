"""
Prologのための標準実装仕様書」で定義されたUMLモデルを
Pydanticモデルとして定義する (ドメインモデル層)
"""

import uuid
from datetime import datetime
from typing import List, Dict, Any, Union, Optional
from pydantic import BaseModel, Field

# -----------------------------------------------
# 4. Prologマッピング - 範囲定義 (Extent)
# -----------------------------------------------

# 4.1. GeographicExtent (Union型)
# (Prolog: geographic_extent_is_description, _is_point, _is_surface)
class GeoExtentDescription(BaseModel):
    description: str = Field(..., description="記述 (例: 竹島エリア)")

class GeoExtentPoint(BaseModel):
    lat: float
    lon: float

class GeoExtentSurface(BaseModel):
    wkt: str = Field(..., description="WKT形式のポリゴン")

# PydanticのUnion型で <<Union>> ステレオタイプを表現
GeographicExtent = Union[GeoExtentDescription, GeoExtentPoint, GeoExtentSurface]


# 4.2. TemporalExtent (確率的モデル)
# (Prolog: temporal_extent_is_beta_distribution, _is_instant)
class TemporalExtentBetaDistribution(BaseModel):
    description: str = Field(..., description="UMLの expected (例: 1950年代頃)")
    start_instant: datetime = Field(..., description="論議領域の開始 (UMLの open)")
    end_instant: datetime = Field(..., description="論議領域の終了 (UMLの close)")
    alpha: float = Field(..., description="ベータ分布の形状パラメータα")
    beta: float = Field(..., description="ベータ分布の形状パラメータβ")

class TemporalExtentInstant(BaseModel):
    instant: datetime = Field(..., description="厳密な日付")

# PydanticのUnion型で、確率的または厳密な日付を表現
TemporalExtent = Union[TemporalExtentBetaDistribution, TemporalExtentInstant]


# -----------------------------------------------
# 5. Prologマッピング - CustomClass (階層型EAV)
# -----------------------------------------------

class Attribute(BaseModel):
    """
    UMLの Attributes クラス
    (Prolog: attribute_value)
    """
    id: str = Field(default_factory=lambda: f"attr_{uuid.uuid4().hex[:8]}")
    key: str
    value: Any
    datatype: str
    description: str = ""
    # UMLの自己参照 (AttributeOfAttribute)
    children: List['Attribute'] = Field(default_factory=list)

class CustomClass(BaseModel):
    """
    UMLの CustomClass クラス
    (Prolog: custom_class)
    """
    id: str = Field(default_factory=lambda: f"cclass_{uuid.uuid4().hex[:8]}")
    classname: str
    # UMLの CustomClass *--> Attributes
    attributes: List[Attribute] = Field(default_factory=list)
    # UMLの自己参照 (ClassOfClass)
    children: List['CustomClass'] = Field(default_factory=list)


# -----------------------------------------------
# 3. Prologマッピング - 主要クラス
# -----------------------------------------------

class SourceMetadata(BaseModel):
    """
    3.2. SourceMetadata クラス (集約される側)
    """
    id: str = Field(default_factory=lambda: f"src_{uuid.uuid4().hex[:8]}")
    # (Prolog: has_citation, has_reference_system)
    citation_id: str # CI_Citationの実体はPrologが管理
    reference_system_id: str # MD_ReferenceSystemの実体はPrologが管理
    
    # (Prolog: source_attribute)
    additional_temporal_extent: Optional[Any] = None
    additional_geographic_extent: Optional[Any] = None

class ContentsMetadata(BaseModel):
    """
    3.3. ContentsMetadata クラス (コンポジションされる側)
    """
    id: str = Field(default_factory=lambda: f"cont_{uuid.uuid4().hex[:8]}")
    
    # (Prolog: contents_attribute)
    abstract: str
    topic_category: str
    
    # (Prolog: has_keyword)
    keyword_ids: List[str] # MD_Keywordsの実体はPrologが管理
    
    # (Prolog: has_geographic_extent)
    geographic_extent: GeographicExtent
    
    # (Prolog: has_temporal_extent)
    temporal_extent: TemporalExtent
    
    # (Prolog: aggregates_custom)
    custom_class_root: Optional[CustomClass] = None

class Metadata(BaseModel):
    """
    3.1. Metadata クラス (最上位のコンテナ)
    """
    id: str = Field(default_factory=lambda: f"meta_{uuid.uuid4().hex[:8]}")
    
    # (Prolog: metadata_attribute)
    datastamp: datetime = Field(default_factory=datetime.now)
    language: str = "jpn"
    
    # (Prolog: metadata_contact)
    contact_id: str # CI_Contactの実体はPrologが管理
    
    # --- 関係性の定義 ---
    
    # (Prolog: aggregates_source)
    # (Metadata o--> SourceMetadata)
    source: SourceMetadata
    
    # (Prolog: composes_contents)
    # (Metadata *--> ContentsMetadata)
    contents: ContentsMetadata