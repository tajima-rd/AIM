# iso19115.py

from dataclasses import dataclass, field
from enum import Enum
from typing import (
    List, 
    Dict, 
    Union, 
    Any, 
    Optional
)

# -----------------------------------------------------------------
# Section 1: 連絡先 (CI_Contact) とその構成要素
# (前回の定義)
# -----------------------------------------------------------------

@dataclass
class CI_OnlineResource:
    """オンラインリソース（Webサイトなど）の情報"""
    linkage: str  # URL (例: "https://example.com")
    protocol: Optional[str] = None # 例: "HTTPS"
    name: Optional[str] = None
    description: Optional[str] = None

@dataclass
class CI_Telephone:
    """電話番号"""
    voice: List[str] = field(default_factory=list)
    facsimile: List[str] = field(default_factory=list)

@dataclass
class CI_Address:
    """住所"""
    deliveryPoint: List[str] = field(default_factory=list) # 番地
    city: Optional[str] = None
    administrativeArea: Optional[str] = None # 都道府県
    postalCode: Optional[str] = None
    country: Optional[str] = None
    electronicMailAddress: List[str] = field(default_factory=list) # Eメール

@dataclass
class CI_Contact:
    """連絡先情報 (CI_Contact)"""
    phone: Optional[CI_Telephone] = None
    address: Optional[CI_Address] = None
    onlineResource: Optional[CI_OnlineResource] = None
    hoursOfService: Optional[str] = None
    contactInstructions: Optional[str] = None

# -----------------------------------------------------------------
# Section 2: 責任者 (CI_ResponsibleParty) と役割
# -----------------------------------------------------------------

class CI_RoleCode(str, Enum):
    """
    責任者の役割を示すコードリスト (Enum)
    (よく使われるもの)
    """
    AUTHOR = "author"
    PROCESSOR = "processor"
    PUBLISHER = "publisher"
    OWNER = "owner"
    POINT_OF_CONTACT = "pointOfContact" # 連絡窓口
    PRINCIPAL_INVESTIGATOR = "principalInvestigator" # 研究代表者
    RESOURCE_PROVIDER = "resourceProvider" # リソース提供者
    ORIGINATOR = "originator" # 作成者

    def __str__(self):
        return self.value

@dataclass
class CI_ResponsibleParty:
    """
    責任者（担当者または組織）の情報
    """
    individualName: Optional[str] = None # 個人名
    organisationName: Optional[str] = None # 組織名
    positionName: Optional[str] = None # 役職名
    contactInfo: Optional[CI_Contact] = None # 連絡先 (CI_Contact を利用)
    role: CI_RoleCode = CI_RoleCode.POINT_OF_CONTACT # 役割

# -----------------------------------------------------------------
# Section 3: 引用・日付 (CI_Citation, CI_Date)
# -----------------------------------------------------------------

class CI_DateTypeCode(str, Enum):
    """日付の種類"""
    CREATION = "creation" # 作成日
    PUBLICATION = "publication" # 公表日
    REVISION = "revision" # 改訂日

    def __str__(self):
        return self.value

@dataclass
class CI_Date:
    """日付とその種類"""
    date: str # 日付 (例: "2025-11-05" または "2025-11-05T09:30:00Z")
    dateType: CI_DateTypeCode # 日付の種類

@dataclass
class CI_Citation:
    """
    引用情報 (データセットやドキュメントのタイトルなど)
    """
    title: str # タイトル
    # 日付 (作成日、公表日など)
    date: List[CI_Date] = field(default_factory=list)
    # 識別子 (例: DOI)
    identifier: Optional[str] = None 
    # 責任者 (著者、発行者など)
    citedResponsibleParty: List[CI_ResponsibleParty] = field(default_factory=list)
    # 概要 (ISO 19115 では presentationForm など他の要素もあるが、簡略化)
    abstract: Optional[str] = None 
    

# -----------------------------------------------------------------
# Section 4: キーワード (MD_Keywords)
# -----------------------------------------------------------------

class MD_KeywordTypeCode(str, Enum):
    """キーワードの種類"""
    DISCIPLINE = "discipline" # 分野
    PLACE = "place" # 地名
    STRATUM = "stratum" # 地層・層
    TEMPORAL = "temporal" # 時間
    THEME = "theme" # 主題

    def __str__(self):
        return self.value

@dataclass
class MD_Keywords:
    """キーワードのセット"""
    keywords: List[str] = field(default_factory=list) # キーワードのリスト
    type: Optional[MD_KeywordTypeCode] = None # キーワードの種類
    # (シソーラス (統制語彙集) の情報を加えることも可能)
    # thesaurusName: Optional[CI_Citation] = None


# -----------------------------------------------------------------
# Section 5: メタデータ本体 (MD_Metadata) の骨格
# -----------------------------------------------------------------

@dataclass
class MD_Identification:
    """
    識別情報 (データセットの概要) - 骨格のみ
    実際には MD_DataIdentification などのサブクラスを使うことが多い
    """
    citation: CI_Citation # データセットの引用情報 (タイトルや概要)
    # 連絡窓口 (推奨)
    pointOfContact: List[CI_ResponsibleParty] = field(default_factory=list)
    # キーワード
    descriptiveKeywords: List[MD_Keywords] = field(default_factory=list)
    # (他にも、spatialRepresentationType, temporalExtent など多数の要素がある)


@dataclass
class MD_Metadata:
    """
    ISO 19115 メタデータ全体のコンテナ (骨格)
    """
    # メタデータ自体の識別子
    fileIdentifier: Optional[str] = None
    # メタデータの言語 (例: "jpn")
    language: str = "jpn"
    # メタデータの文字セット (例: "UTF-8")
    characterSet: str = "UTF-8"
    # メタデータの連絡先 (メタデータを作成した人)
    contact: List[CI_ResponsibleParty] = field(default_factory=list)
    # メタデータの日付
    dateStamp: str = "" # 例: "2025-11-05"
    
    # 対象となるデータセットの識別情報
    identificationInfo: List[MD_Identification] = field(default_factory=list)

# -----------------------------------------------------------------
# Section 6: 範囲 (Extent) 関連
# -----------------------------------------------------------------

@dataclass
class EX_GeographicBoundingBox:
    """
    地理的範囲 (四隅の緯度経度)
    """
    westBoundLongitude: float
    eastBoundLongitude: float
    southBoundLatitude: float
    northBoundLatitude: float

@dataclass
class TM_Object:
    """時間オブジェクトの基底 (簡略化)"""
    # ISO 19108 (Temporal Schema) に基づくが、ここでは簡略化
    pass

@dataclass
class TM_Primitive(TM_Object):
    """
    時間プリミティブ (簡略化)
    実際には TM_Instant (特定日時) や TM_Period (期間) を使う
    """
    value: str # 例: "2025-11-05" や "2025-01-01/2025-12-31"

@dataclass
class EX_TemporalExtent:
    """時間的範囲"""
    extent: TM_Primitive

@dataclass
class EX_Extent:
    """
    範囲 (空間的・時間的)
    """
    description: Optional[str] = None # 範囲の説明
    # 地理的範囲 (BBox や Polygon など)
    geographicElement: List[EX_GeographicBoundingBox] = field(default_factory=list)
    # 時間的範囲
    temporalElement: List[EX_TemporalExtent] = field(default_factory=list)
    # 垂直範囲 (例: 高度、水深)
    # verticalElement: List[EX_VerticalExtent] = field(default_factory=list)


# -----------------------------------------------------------------
# Section 7: 制約 (Constraints) 関連
# -----------------------------------------------------------------

class MD_RestrictionCode(str, Enum):
    """制約の種類 (ライセンス、著作権など)"""
    COPYRIGHT = "copyright"
    PATENT = "patent"
    TRADEMARK = "trademark"
    LICENSE = "license"
    INTELLECTUAL_PROPERTY_RIGHTS = "intellectualPropertyRights"
    RESTRICTED = "restricted"
    OTHER_RESTRICTIONS = "otherRestrictions"

    def __str__(self):
        return self.value

@dataclass
class MD_Constraints:
    """制約の基底クラス (簡略化)"""
    useLimitation: List[str] = field(default_factory=list) # 利用上の制限

@dataclass
class MD_LegalConstraints(MD_Constraints):
    """法的制約 (ライセンスなど)"""
    accessConstraints: List[MD_RestrictionCode] = field(default_factory=list) # アクセス制約
    useConstraints: List[MD_RestrictionCode] = field(default_factory=list) # 利用制約
    otherConstraints: List[str] = field(default_factory=list) # その他の制約

@dataclass
class MD_SecurityConstraints(MD_Constraints):
    """セキュリティ制約"""
    classification: Optional[str] = None # (例: "機密", "公開")
    # ... 他のセキュリティ関連フィールド ...


# -----------------------------------------------------------------
# Section 8: 配布 (Distribution) 関連
# -----------------------------------------------------------------

@dataclass
class MD_Format:
    """データ形式"""
    name: str # 形式の名前 (例: "GeoTIFF")
    version: Optional[str] = None # バージョン (例: "1.1")

@dataclass
class MD_DigitalTransferOptions:
    """デジタル転送オプション (ダウンロードURLなど)"""
    unitsOfDistribution: Optional[str] = None # 配布単位 (例: "scene")
    # オンラインリソース (ダウンロードURL, APIエンドポイントなど)
    onLine: List['CI_OnlineResource'] = field(default_factory=list) # CI_OnlineResourceは定義済みと仮定

@dataclass
class MD_Distribution:
    """配布情報"""
    # 配布形式
    distributionFormat: List[MD_Format] = field(default_factory=list)
    # 転送オプション (ダウンロード方法)
    transferOptions: List[MD_DigitalTransferOptions] = field(default_factory=list)


# -----------------------------------------------------------------
# Section 9: データの識別 (MD_DataIdentification)
# (MD_Identification を具体化)
# -----------------------------------------------------------------

class MD_ProgressCode(str, Enum):
    """データの状態 (完成、作業中など)"""
    COMPLETED = "completed"
    ON_GOING = "onGoing"
    PLANNED = "planned"

    def __str__(self):
        return self.value

@dataclass
class MD_Resolution:
    """解像度 (簡略化)"""
    # 実際には equivalentScale (縮尺) や distance (距離) など
    value: str # 例: "10m" や "1:25000"

@dataclass
class MD_Identification:
    """
    識別情報 (基底クラス)
    (以前の骨格定義から、必要なものを追加・修正)
    """
    citation: 'CI_Citation' # 引用情報 (CI_Citationは定義済みと仮定)
    abstract: str # 概要
    pointOfContact: List['CI_ResponsibleParty'] = field(default_factory=list) # CI_ResponsiblePartyは定義済み
    descriptiveKeywords: List['MD_Keywords'] = field(default_factory=list) # MD_Keywordsは定義済み
    # 制約
    resourceConstraints: List[Union[MD_LegalConstraints, MD_SecurityConstraints, MD_Constraints]] = field(default_factory=list)
    # (その他多くのフィールド...)


@dataclass
class MD_DataIdentification(MD_Identification):
    """
    データセットの具体的な識別情報
    (MD_Identification を継承)
    """
    # 空間的範囲
    extent: List[EX_Extent] = field(default_factory=list)
    # データの状態 (完成、作業中など)
    status: List[MD_ProgressCode] = field(default_factory=list)
    # 空間解像度
    spatialResolution: List[MD_Resolution] = field(default_factory=list)
    # 言語 (データ本体の言語)
    language: List[str] = field(default_factory=list) # 例: ["jpn"]
    # 文字セット
    characterSet: List[str] = field(default_factory=list) # 例: ["UTF-8"]
    # (トピックカテゴリ (MD_TopicCategoryCode) なども一般的)


# -----------------------------------------------------------------
# Section 10: 品質 (Data Quality) 関連
# -----------------------------------------------------------------

class DQ_EvaluationMethodTypeCode(str, Enum):
    """品質評価の方法"""
    DIRECT = "direct" # 直接評価
    INDIRECT = "indirect" # 間接評価

    def __str__(self):
        return self.value

@dataclass
class DQ_Scope:
    """品質評価の適用範囲"""
    level: str # 例: "dataset"
    # (実際には levelDescription など、より詳細な定義が可能)

@dataclass
class DQ_Element:
    """
    品質要素 (基底クラス)
    (実際には DQ_Completeness, DQ_Accuracy などのサブクラスを使う)
    """
    nameOfMeasure: Optional[str] = None # 品質の尺度名
    evaluationMethodType: Optional[DQ_EvaluationMethodTypeCode] = None
    # ... (評価結果 (DQ_Result) など) ...

@dataclass
class DQ_DataQuality:
    """データ品質セクション"""
    scope: DQ_Scope # 品質評価の範囲
    report: List[DQ_Element] = field(default_factory=list) # 品質の報告
    # (品質の概要 (lineage) などもここに含まれる)