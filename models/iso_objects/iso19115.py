# iso19115.py
import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import (
    List, 
    Dict, 
    Union, 
    Any, 
    Optional
)


class CI_OnlineResource:
    """オンラインリソース（Webサイトなど）の情報"""
    def __init__(self,
                 linkage: str,  # URL (例: "https://example.com")
                 protocol: Optional[str] = None, # 例: "HTTPS"
                 name: Optional[str] = None,
                 description: Optional[str] = None
                ):
        self.linkage = linkage
        self.protocol = protocol
        self.name = name
        self.description = description
    
    @classmethod
    def load_from_dict(cls, data: Dict[str, Any]) -> "CI_Address":
        if not data:
            return None
        return cls(**data)

    def __repr__(self) -> str:
        parts = [f"linkage='{self.linkage}'"]
        if self.protocol: parts.append(f"protocol='{self.protocol}'")
        if self.name: parts.append(f"name='{self.name}'")
        if self.description: parts.append(f"description='{self.description}'")
        return f"CI_OnlineResource({', '.join(parts)})"

class CI_Telephone:
    def __init__(self,
                 voice: List[str] = None,
                 facsimile: List[str] = None
                ):
        # default_factory=list の動作を再現 (ミュータブルなデフォルト引数を避ける)
        self.voice = voice if voice is not None else []
        self.facsimile = facsimile if facsimile is not None else []

    @classmethod
    def load_from_dict(cls, data: Dict[str, Any]) -> "CI_Address":
        if not data:
            return None
        return cls(**data)
    
    def __repr__(self) -> str:
        parts = []
        if self.voice: parts.append(f"voice={self.voice}")
        if self.facsimile: parts.append(f"facsimile={self.facsimile}")
        return f"CI_Telephone({', '.join(parts)})"

class CI_Address:
    """住所"""
    def __init__(self,
                 deliveryPoint: List[str] = None, # 番地
                 city: Optional[str] = None,
                 administrativeArea: Optional[str] = None, # 都道府県
                 postalCode: Optional[str] = None,
                 country: Optional[str] = None,
                 electronicMailAddress: List[str] = None # Eメール
                ):
        # default_factory=list の動作を再現
        self.deliveryPoint = deliveryPoint if deliveryPoint is not None else []
        self.city = city
        self.administrativeArea = administrativeArea
        self.postalCode = postalCode
        self.country = country
        self.electronicMailAddress = electronicMailAddress if electronicMailAddress is not None else []

    @classmethod
    def load_from_dict(cls, data: Dict[str, Any]) -> "CI_Address":
        if not data:
            return None
        return cls(**data)
    
    def __repr__(self) -> str:
        parts = []
        if self.deliveryPoint: parts.append(f"deliveryPoint={self.deliveryPoint}")
        if self.city: parts.append(f"city='{self.city}'")
        if self.administrativeArea: parts.append(f"administrativeArea='{self.administrativeArea}'")
        if self.postalCode: parts.append(f"postalCode='{self.postalCode}'")
        if self.country: parts.append(f"country='{self.country}'")
        if self.electronicMailAddress: parts.append(f"electronicMailAddress={self.electronicMailAddress}")
        return f"CI_Address({', '.join(parts)})"

class CI_Contact:
    """
    連絡先情報 (CI_Contact) - ISO標準構造 (通常のクラス)
    """
    
    def __init__(self, 
                 phone: Optional[CI_Telephone] = None,
                 address: Optional[CI_Address] = None,
                 onlineResource: Optional[CI_OnlineResource] = None,
                 hoursOfService: Optional[str] = None,
                 contactInstructions: Optional[str] = None
                ):
        
        # ISO標準フィールドをそのまま初期化
        self.phone = phone
        self.address = address
        self.onlineResource = onlineResource
        self.hoursOfService = hoursOfService
        self.contactInstructions = contactInstructions
    
    @classmethod
    def load_from_dict(cls, data: Dict[str, Any]) -> "CI_Contact":
        if not data:
            return None

        # ネストされた辞書データを取得
        phone_data = data.get('phone')
        address_data = data.get('address')
        online_resource_data = data.get('onlineResource')
        phone_instance = None
        if phone_data:
            try:
                phone_instance = CI_Telephone.load_from_dict(phone_data)
            except (NameError, AttributeError):
                try:
                    phone_instance = CI_Telephone(**phone_data)
                except NameError:
                    phone_instance = phone_data # フォールバック

        address_instance = None
        if address_data:
            try:
                address_instance = CI_Address.load_from_dict(address_data)
            except (NameError, AttributeError):
                try:
                    address_instance = CI_Address(**address_data)
                except NameError:
                    address_instance = address_data # フォールバック

        online_resource_instance = None
        if online_resource_data:
            try:
                online_resource_instance = CI_OnlineResource.load_from_dict(online_resource_data)
            except (NameError, AttributeError):
                try:
                    online_resource_instance = CI_OnlineResource(**online_resource_data)
                except NameError:
                    online_resource_instance = online_resource_data # フォールバック

        return cls(
            phone=phone_instance,
            address=address_instance,
            onlineResource=online_resource_instance,
            hoursOfService=data.get('hoursOfService'),
            contactInstructions=data.get('contactInstructions')
        )
                
    def __repr__(self) -> str:
        """
        デバッグ用の簡易的な __repr__
        """
        parts = []
        if self.phone: parts.append(f"phone={self.phone}")
        if self.address: parts.append(f"address={self.address}")
        if self.onlineResource: parts.append(f"onlineResource={self.onlineResource}")
        if self.hoursOfService: parts.append(f"hoursOfService='{self.hoursOfService}'")
        if self.contactInstructions: parts.append(f"contactInstructions='{self.contactInstructions}'")
        
        return f"CI_Contact({', '.join(parts)})"

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

class CI_ResponsibleParty:
    """
    責任者（担当者または組織）の情報
    """
    def __init__(self,
                 individualName: Optional[str] = None, # 個人名
                 organisationName: Optional[str] = None, # 組織名
                 positionName: Optional[str] = None, # 役職名
                 contactInfo: Optional['CI_Contact'] = None, # 連絡先
                 role: 'CI_RoleCode' = CI_RoleCode.POINT_OF_CONTACT # 役割
                ):
        self.individualName = individualName
        self.organisationName = organisationName
        self.positionName = positionName
        self.contactInfo = contactInfo
        self.role = role

    def __repr__(self) -> str:
        name = self.individualName or self.organisationName or "N/A"
        return f"CI_ResponsibleParty(name='{name}', role={self.role})"

# -----------------------------------------------------------------
# Section 3: 引用・日付 (CI_Citation, CI_Date)
# -----------------------------------------------------------------
class CI_Date:
    """日付とその種類"""
    def __init__(self,
                 date: str, # 日付 (例: "2025-11-05")
                 dateType: 'CI_DateTypeCode' # 日付の種類
                ):
        self.date = date
        self.dateType = dateType

    def __repr__(self) -> str:
        return f"CI_Date(date='{self.date}', dateType={self.dateType})"

class CI_DateTypeCode(str, Enum):
    """日付の種類"""
    CREATION = "creation"
    PUBLICATION = "publication"
    REVISION = "revision"

    def __str__(self):
        return self.value

class CI_PresentationFormCode(str, Enum):
    """
    引用情報の表現形式（ISO 19115）
    (以前の簡略化で欠落していたクラス)
    """
    DOCUMENT_DIGITAL = "documentDigital"
    DOCUMENT_HARDCOPY = "documentHardcopy"
    IMAGE_DIGITAL = "imageDigital"
    IMAGE_HARDCOPY = "imageHardcopy"
    MAP_DIGITAL = "mapDigital"
    MAP_HARDCOPY = "mapHardcopy"
    MODEL_DIGITAL = "modelDigital"
    MODEL_HARDCOPY = "modelHardcopy"
    # ... 他にも多数 ...
    TABLE_DIGITAL = "tableDigital"
    TABLE_HARDCOPY = "tableHardcopy"

    def __str__(self):
        return self.value

class MD_Identifier:
    """
    識別子（ISO 19115）
    (以前は 'Optional[str]' に簡略化されていたクラス)
    
    (注: 本来 MD_Identifier は MD_Identification よりも複雑な
     authority, codeSpace などを持つ 'RS_Identifier' を参照しますが、
     ここでは CI_Citation で最低限必要な 'code' のみを実装します)
    """
    def __init__(self,
                 code: str,
                 # authority: Optional[CI_Citation] = None, # (権威)
                 # codeSpace: Optional[str] = None
                ):
        self.code = code # 識別子 (例: "doi:10.1000/xyz")

    def __repr__(self) -> str:
        return f"MD_Identifier(code='{self.code}')"

class CI_Series:
    """
    シリーズ（叢書）情報（ISO 19115）
    (以前の簡略化で欠落していたクラス)
    """
    def __init__(self,
                 name: Optional[str] = None,
                 issueIdentification: Optional[str] = None, # 号数
                 page: Optional[str] = None # ページ
                ):
        self.name = name
        self.issueIdentification = issueIdentification
        self.page = page

    def __repr__(self) -> str:
        parts = []
        if self.name: parts.append(f"name='{self.name}'")
        if self.issueIdentification: parts.append(f"issueIdentification='{self.issueIdentification}'")
        if self.page: parts.append(f"page='{self.page}'")
        return f"CI_Series({', '.join(parts)})"

class CI_Citation:
    """
    引用情報 (データセットやドキュメントのタイトルなど)
    (ISO 19115 の定義に基づき「完全な」実装)
    """
    
    def __init__(self,
                 title: str, # タイトル
                 date: Optional[List['CI_Date']] = None,                 
                 alternateTitle: Optional[List[str]] = None, # 別名
                 edition: Optional[str] = None, # 版
                 editionDate: Optional[str] = None, # 版の日付 (ISO 8601)
                 identifier: Optional['MD_Identifier'] = None, 
                 citedResponsibleParty: Optional[List['CI_ResponsibleParty']] = None,
                 presentationForm: Optional[List[CI_PresentationFormCode]] = None,
                 series: Optional['CI_Series'] = None,
                 otherCitationDetails: Optional[List[str]] = None, # その他
                 collectiveTitle: Optional[str] = None, # (収集)
                 ISBN: Optional[str] = None,
                 ISSN: Optional[str] = None,
                 abstract: Optional[str] = None
                ):
        
        self.title = title
        self.date = date if date is not None else []
        self.alternateTitle = alternateTitle if alternateTitle is not None else []
        self.edition = edition
        self.editionDate = editionDate
        self.identifier = identifier
        self.citedResponsibleParty = citedResponsibleParty if citedResponsibleParty is not None else []
        self.presentationForm = presentationForm if presentationForm is not None else []
        self.series = series
        self.otherCitationDetails = otherCitationDetails if otherCitationDetails is not None else []
        self.collectiveTitle = collectiveTitle
        self.ISBN = ISBN
        self.ISSN = ISSN
        self.abstract = abstract

    def __repr__(self) -> str:
        # (フィールドが多すぎるため、主要なもののみ表示)
        parts = [f"title='{self.title}'"]
        if self.date: parts.append(f"date={self.date}")
        if self.identifier: parts.append(f"identifier={self.identifier}")
        if self.presentationForm: parts.append(f"presentationForm={self.presentationForm}")
        if self.abstract: parts.append(f"abstract='{self.abstract[:20]}...'")
        
        return f"CI_Citation({', '.join(parts)})"

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

class MD_Keywords:
    """キーワードのセット"""
    def __init__(self,
                 keywords: Optional[List[str]] = None,
                 type: Optional['MD_KeywordTypeCode'] = None
                 # thesaurusName: Optional['CI_Citation'] = None
                ):
        self.keywords = keywords if keywords is not None else []
        self.type = type

    def __repr__(self) -> str:
        count = len(self.keywords)
        return f"MD_Keywords(type={self.type}, count={count})"

# -----------------------------------------------------------------
# Section 5: メタデータ本体 (MD_Metadata) の骨格
# -----------------------------------------------------------------

class MD_Identification:
    """
    識別情報 (基底クラス)
    """
    def __init__(self,
                 citation: 'CI_Citation',
                 abstract: str,
                 pointOfContact: Optional[List['CI_ResponsibleParty']] = None,
                 descriptiveKeywords: Optional[List['MD_Keywords']] = None,
                 resourceConstraints: Optional[List[Union['MD_LegalConstraints', 'MD_SecurityConstraints', 'MD_Constraints']]] = None,
                 # (ISO 19115 の追加フィールド)
                 purpose: Optional[str] = None,
                 status: Optional[List['MD_ProgressCode']] = None, # (MD_ProgressCode は Section 9 で定義済)
                 graphicOverview: Optional[List[str]] = None, # (MD_BrowseGraphic)
                 resourceMaintenance: Optional[List['MD_MaintenanceInformation']] = None,
                 # ... 他にも多数のフィールド ...
                ):
        self.citation = citation
        self.abstract = abstract
        self.pointOfContact = pointOfContact if pointOfContact is not None else []
        self.descriptiveKeywords = descriptiveKeywords if descriptiveKeywords is not None else []
        self.resourceConstraints = resourceConstraints if resourceConstraints is not None else []
        self.purpose = purpose
        self.status = status if status is not None else []
        self.graphicOverview = graphicOverview if graphicOverview is not None else []
        self.resourceMaintenance = resourceMaintenance if resourceMaintenance is not None else []

    def __repr__(self) -> str:
        return f"MD_Identification(title='{self.citation.title}')"

# -----------------------------------------------------------------
# Section 5: メタデータ本体 (MD_Metadata) の「完全な」実装
# -----------------------------------------------------------------

class MD_CharacterSetCode(str, Enum):
    """
    文字セットコード (ISO 19115)
    (以前の簡略化で欠落していた Enum)
    """
    UCS_2 = "ucs2"
    UCS_4 = "ucs4"
    UTF_7 = "utf7"
    UTF_8 = "utf8" # 一般的
    UTF_16 = "utf16"
    UTF_16BE = "utf16be"
    UTF_16LE = "utf16le"
    SHIFT_JIS = "shiftJIS" # 日本
    EUC_JP = "eucJP" # 日本
    # ... 他にも多数 ...
    
    def __str__(self):
        return self.value

class MD_ScopeCode(str, Enum):
    """
    メタデータの階層レベル（範囲） (ISO 19115)
    (以前の簡略化で欠落していた Enum)
    """
    ATTRIBUTE = "attribute"
    ATTRIBUTE_TYPE = "attributeType"
    COLLECTION_HARDWARE = "collectionHardware"
    COLLECTION_SESSION = "collectionSession"
    DATASET = "dataset" # データセット
    SERIES = "series" # シリーズ
    NON_GEOGRAPHIC_DATASET = "nonGeographicDataset"
    DIMENSION_GROUP = "dimensionGroup"
    FEATURE = "feature"
    FEATURE_TYPE = "featureType"
    PROPERTY_TYPE = "propertyType"
    FIELD_SESSION = "fieldSession"
    SOFTWARE = "software"
    SERVICE = "service"
    MODEL = "model"
    TILE = "tile"
    
    def __str__(self):
        return self.value

# -----------------------------------------------------------------
# Section 4: 参照系 (MD_ReferenceSystem, MD_SpatialRepresentation)
# (MD_Metadata が参照する未定義クラス)
# -----------------------------------------------------------------

class MD_SpatialRepresentation:
    """
    (抽象クラス) 空間表現のメカニズム (ISO 19115)
    (MD_VectorSpatialRepresentation, MD_GridSpatialRepresentation などが継承)
    """
    def __init__(self):
        # 抽象クラスのため、共通フィールドは定義しない
        pass

    def __repr__(self) -> str:
        return "MD_SpatialRepresentation (Abstract)"

class MD_ReferenceSystem:
    """
    (抽象クラス) 空間参照系 (ISO 19115)
    (RS_Identifier を持つが、ここでは基底として定義)
    """
    def __init__(self,
                 referenceSystemIdentifier: Optional['MD_Identifier'] = None
                ):
        self.referenceSystemIdentifier = referenceSystemIdentifier

    def __repr__(self) -> str:
        return f"MD_ReferenceSystem (Abstract, id={self.referenceSystemIdentifier})"

# -----------------------------------------------------------------
# Section 5: メタデータ拡張 (MD_MetadataExtensionInformation)
# (MD_Metadata が参照する未定義クラス)
# -----------------------------------------------------------------

class MD_ObligationCode(str, Enum):
    """義務コード (ISO 19115)"""
    MANDATORY = "mandatory"
    OPTIONAL = "optional"
    CONDITIONAL = "conditional"

    def __str__(self):
        return self.value

class MD_DatatypeCode(str, Enum):
    """データ型コード (ISO 19115) - 主要なもの"""
    CLASS = "class"
    CODE_LIST = "codeList"
    ENUMERATION = "enumeration"
    CHARACTER_STRING = "characterString"
    INTEGER = "integer"
    REAL = "real"
    BOOLEAN = "boolean"
    # ... 他多数 ...

    def __str__(self):
        return self.value

class MD_ExtendedElementInformation:
    """メタデータ拡張要素の情報 (ISO 19115)"""
    def __init__(self,
                 name: str,
                 definition: str,
                 dataType: MD_DatatypeCode,
                 shortName: Optional[str] = None,
                 domainCode: Optional[int] = None,
                 obligation: Optional[MD_ObligationCode] = None,
                 condition: Optional[str] = None,
                 maximumOccurrence: Optional[str] = None,
                 domainValue: Optional[str] = None,
                 parentEntity: Optional[List[str]] = None,
                 rule: Optional[str] = None,
                 rationale: Optional[List[str]] = None,
                 source: Optional['CI_ResponsibleParty'] = None
                ):
        self.name = name
        self.definition = definition
        self.dataType = dataType
        self.shortName = shortName
        self.domainCode = domainCode
        self.obligation = obligation
        self.condition = condition
        self.maximumOccurrence = maximumOccurrence
        self.domainValue = domainValue
        self.parentEntity = parentEntity if parentEntity is not None else []
        self.rule = rule
        self.rationale = rationale if rationale is not None else []
        self.source = source

    def __repr__(self) -> str:
        return f"MD_ExtendedElementInformation(name='{self.name}', dataType={self.dataType})"

class MD_MetadataExtensionInformation:
    """メタデータ拡張情報 (ISO 19115)"""
    def __init__(self,
                 extensionOnLineResource: Optional['CI_OnlineResource'] = None,
                 extendedElementInformation: Optional[List[MD_ExtendedElementInformation]] = None
                ):
        self.extensionOnLineResource = extensionOnLineResource
        self.extendedElementInformation = extendedElementInformation if extendedElementInformation is not None else []

    def __repr__(self) -> str:
        count = len(self.extendedElementInformation) if self.extendedElementInformation else 0
        return f"MD_MetadataExtensionInformation(elements={count})"

# -----------------------------------------------------------------
# Section X: リソース内容 (MD_ContentInformation)
# (MD_Metadata が参照する未定義クラス)
# -----------------------------------------------------------------

class MD_ContentInformation:
    """
    (抽象クラス) リソースの内容 (ISO 19115)
    (MD_FeatureCatalogueDescription, MD_CoverageDescription などが継承)
    """
    def __init__(self):
        # 抽象クラス
        pass

    def __repr__(self) -> str:
        return "MD_ContentInformation (Abstract)"

# -----------------------------------------------------------------
# Section X: 描画・スキーマ・保守・利用法・スコープ
# (MD_Metadata が参照する残りの未定義クラス)
# -----------------------------------------------------------------

class MD_PortrayalCatalogueReference:
    """描画カタログ参照 (ISO 19115)"""
    def __init__(self,
                 portrayalCatalogueCitation: 'CI_Citation'
                ):
        self.portrayalCatalogueCitation = portrayalCatalogueCitation

    def __repr__(self) -> str:
        return f"MD_PortrayalCatalogueReference(title='{self.portrayalCatalogueCitation.title}')"

class MD_ApplicationSchemaInformation:
    """アプリケーションスキーマ情報 (ISO 19115)"""
    def __init__(self,
                 name: 'CI_Citation',
                 schemaLanguage: str,
                 constraintLanguage: str,
                 schemaAscii: Optional[str] = None,
                 graphicsFile: Optional[str] = None, # (Base64 or URI)
                 softwareDevelopmentFile: Optional[str] = None, # (Base64 or URI)
                 softwareDevelopmentFileFormat: Optional[str] = None
                ):
        self.name = name
        self.schemaLanguage = schemaLanguage
        self.constraintLanguage = constraintLanguage
        self.schemaAscii = schemaAscii
        self.graphicsFile = graphicsFile
        self.softwareDevelopmentFile = softwareDevelopmentFile
        self.softwareDevelopmentFileFormat = softwareDevelopmentFileFormat

    def __repr__(self) -> str:
        return f"MD_ApplicationSchemaInformation(name='{self.name.title}')"

class MD_MaintenanceFrequencyCode(str, Enum):
    """保守（更新）頻度コード (ISO 19115)"""
    CONTINUAL = "continual"
    DAILY = "daily"
    WEEKLY = "weekly"
    FORTNIGHTLY = "fortnightly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    BIANNUALLY = "biannually"
    ANNUALLY = "annually"
    AS_NEEDED = "asNeeded"
    IRREGULAR = "irregular"
    NOT_PLANNED = "notPlanned"
    UNKNOWN = "unknown"

    def __str__(self):
        return self.value

class MD_ScopeDescription:
    """スコープ（範囲）の詳細記述 (ISO 19115)"""
    def __init__(self,
                 attributes: Optional[List[str]] = None,
                 features: Optional[List[str]] = None,
                 featureInstances: Optional[List[str]] = None,
                 attributeInstances: Optional[List[str]] = None,
                 dataset: Optional[str] = None,
                 other: Optional[str] = None
                ):
        self.attributes = attributes if attributes is not None else []
        self.features = features if features is not None else []
        self.featureInstances = featureInstances if featureInstances is not None else []
        self.attributeInstances = attributeInstances if attributeInstances is not None else []
        self.dataset = dataset
        self.other = other

    def __repr__(self) -> str:
        return f"MD_ScopeDescription(dataset='{self.dataset}', other='{self.other}')"

class MD_MaintenanceInformation:
    """保守情報 (ISO 19115)"""
    def __init__(self,
                 maintenanceAndUpdateFrequency: MD_MaintenanceFrequencyCode,
                 dateOfNextUpdate: Optional[str] = None,
                 userDefinedMaintenanceFrequency: Optional[str] = None, # (TM_Period を文字列で代用)
                 updateScope: Optional[List['MD_ScopeCode']] = None, # (MD_ScopeCode は Section 5 で定義済)
                 updateScopeDescription: Optional[List[MD_ScopeDescription]] = None,
                 maintenanceNote: Optional[List[str]] = None,
                 contact: Optional[List['CI_ResponsibleParty']] = None
                ):
        self.maintenanceAndUpdateFrequency = maintenanceAndUpdateFrequency
        self.dateOfNextUpdate = dateOfNextUpdate
        self.userDefinedMaintenanceFrequency = userDefinedMaintenanceFrequency
        self.updateScope = updateScope if updateScope is not None else []
        self.updateScopeDescription = updateScopeDescription if updateScopeDescription is not None else []
        self.maintenanceNote = maintenanceNote if maintenanceNote is not None else []
        self.contact = contact if contact is not None else []

    def __repr__(self) -> str:
        return f"MD_MaintenanceInformation(frequency={self.maintenanceAndUpdateFrequency})"

class MD_Usage:
    """リソースの利用法 (ISO 19115)"""
    def __init__(self,
                 specificUsage: str,
                 userDeterminedLimitations: Optional[str] = None,
                 userContactInfo: Optional[List['CI_ResponsibleParty']] = None,
                 response: Optional[str] = None
                ):
        self.specificUsage = specificUsage
        self.userDeterminedLimitations = userDeterminedLimitations
        self.userContactInfo = userContactInfo if userContactInfo is not None else []
        self.response = response

    def __repr__(self) -> str:
        return f"MD_Usage(specificUsage='{self.specificUsage}')"


# --- Section 4: 参照系 (MD_ReferenceSystem) ---
class MD_SpatialRepresentation:
    """
    (抽象クラス) 空間表現のメカニズム (ISO 19115)
    (MD_VectorSpatialRepresentation, MD_GridSpatialRepresentation などが継承)
    """
    def __init__(self):
        pass # 抽象クラス
    def __repr__(self) -> str:
        return "MD_SpatialRepresentation (Abstract)"

class MD_ReferenceSystem:
    """
    (抽象クラス) 空間参照系 (ISO 19115)
    (RS_Identifier を持つが、ここでは基底として定義)
    """
    def __init__(self,
                 referenceSystemIdentifier: Optional['MD_Identifier'] = None
                ):
        self.referenceSystemIdentifier = referenceSystemIdentifier
    def __repr__(self) -> str:
        return f"MD_ReferenceSystem (Abstract, id={self.referenceSystemIdentifier})"

# --- Section 5: メタデータ拡張 (MD_MetadataExtensionInformation) ---
class MD_ObligationCode(str, Enum):
    """(依存Enum) 義務コード (ISO 19115)"""
    MANDATORY = "mandatory"
    OPTIONAL = "optional"
    CONDITIONAL = "conditional"
    def __str__(self): return self.value

class MD_DatatypeCode(str, Enum):
    """(依存Enum) データ型コード (ISO 19115) - 主要なもの"""
    CLASS = "class"
    CODE_LIST = "codeList"
    ENUMERATION = "enumeration"
    CHARACTER_STRING = "characterString"
    INTEGER = "integer"
    REAL = "real"
    BOOLEAN = "boolean"
    def __str__(self): return self.value

class MD_ExtendedElementInformation:
    """(依存クラス) メタデータ拡張要素の情報 (ISO 19115)"""
    def __init__(self,
                 name: str,
                 definition: str,
                 dataType: MD_DatatypeCode,
                 shortName: Optional[str] = None,
                 domainCode: Optional[int] = None,
                 obligation: Optional[MD_ObligationCode] = None,
                 condition: Optional[str] = None,
                 maximumOccurrence: Optional[str] = None,
                 domainValue: Optional[str] = None,
                 parentEntity: Optional[List[str]] = None,
                 rule: Optional[str] = None,
                 rationale: Optional[List[str]] = None,
                 source: Optional['CI_ResponsibleParty'] = None
                ):
        self.name = name
        self.definition = definition
        self.dataType = dataType
        self.shortName = shortName
        self.domainCode = domainCode
        self.obligation = obligation
        self.condition = condition
        self.maximumOccurrence = maximumOccurrence
        self.domainValue = domainValue
        self.parentEntity = parentEntity if parentEntity is not None else []
        self.rule = rule
        self.rationale = rationale if rationale is not None else []
        self.source = source
    def __repr__(self) -> str:
        return f"MD_ExtendedElementInformation(name='{self.name}', dataType={self.dataType})"

class MD_MetadataExtensionInformation:
    """メタデータ拡張情報 (ISO 19115)"""
    def __init__(self,
                 extensionOnLineResource: Optional['CI_OnlineResource'] = None,
                 extendedElementInformation: Optional[List[MD_ExtendedElementInformation]] = None
                ):
        self.extensionOnLineResource = extensionOnLineResource
        self.extendedElementInformation = extendedElementInformation if extendedElementInformation is not None else []
    def __repr__(self) -> str:
        count = len(self.extendedElementInformation) if self.extendedElementInformation else 0
        return f"MD_MetadataExtensionInformation(elements={count})"

# --- Section X: リソース内容 (MD_ContentInformation) ---
class MD_ContentInformation:
    """
    (抽象クラス) リソースの内容 (ISO 19115)
    (MD_FeatureCatalogueDescription, MD_CoverageDescription などが継承)
    """
    def __init__(self):
        pass # 抽象クラス
    def __repr__(self) -> str:
        return "MD_ContentInformation (Abstract)"

# --- Section X: 描画・スキーマ・保守・利用法・スコープ (残りの未定義クラス) ---
class MD_PortrayalCatalogueReference:
    """描画カタログ参照 (ISO 19115)"""
    def __init__(self,
                 portrayalCatalogueCitation: 'CI_Citation'
                ):
        self.portrayalCatalogueCitation = portrayalCatalogueCitation
    def __repr__(self) -> str:
        return f"MD_PortrayalCatalogueReference(title='{self.portrayalCatalogueCitation.title}')"

class MD_ApplicationSchemaInformation:
    """アプリケーションスキーマ情報 (ISO 19115)"""
    def __init__(self,
                 name: 'CI_Citation',
                 schemaLanguage: str,
                 constraintLanguage: str,
                 schemaAscii: Optional[str] = None,
                 graphicsFile: Optional[str] = None,
                 softwareDevelopmentFile: Optional[str] = None,
                 softwareDevelopmentFileFormat: Optional[str] = None
                ):
        self.name = name
        self.schemaLanguage = schemaLanguage
        self.constraintLanguage = constraintLanguage
        self.schemaAscii = schemaAscii
        self.graphicsFile = graphicsFile
        self.softwareDevelopmentFile = softwareDevelopmentFile
        self.softwareDevelopmentFileFormat = softwareDevelopmentFileFormat
    def __repr__(self) -> str:
        return f"MD_ApplicationSchemaInformation(name='{self.name.title}')"

class MD_MaintenanceFrequencyCode(str, Enum):
    """(依存Enum) 保守（更新）頻度コード (ISO 19115)"""
    CONTINUAL = "continual"
    DAILY = "daily"
    WEEKLY = "weekly"
    FORTNIGHTLY = "fortnightly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    BIANNUALLY = "biannually"
    ANNUALLY = "annually"
    AS_NEEDED = "asNeeded"
    IRREGULAR = "irregular"
    NOT_PLANNED = "notPlanned"
    UNKNOWN = "unknown"
    def __str__(self): return self.value

class MD_ScopeDescription:
    """(依存クラス) スコープ（範囲）の詳細記述 (ISO 19115)"""
    def __init__(self,
                 attributes: Optional[List[str]] = None,
                 features: Optional[List[str]] = None,
                 featureInstances: Optional[List[str]] = None,
                 attributeInstances: Optional[List[str]] = None,
                 dataset: Optional[str] = None,
                 other: Optional[str] = None
                ):
        self.attributes = attributes if attributes is not None else []
        self.features = features if features is not None else []
        self.featureInstances = featureInstances if featureInstances is not None else []
        self.attributeInstances = attributeInstances if attributeInstances is not None else []
        self.dataset = dataset
        self.other = other
    def __repr__(self) -> str:
        return f"MD_ScopeDescription(dataset='{self.dataset}', other='{self.other}')"

class MD_MaintenanceInformation:
    """保守情報 (ISO 19115)"""
    def __init__(self,
                 maintenanceAndUpdateFrequency: MD_MaintenanceFrequencyCode,
                 dateOfNextUpdate: Optional[str] = None,
                 userDefinedMaintenanceFrequency: Optional[str] = None, 
                 updateScope: Optional[List['MD_ScopeCode']] = None, 
                 updateScopeDescription: Optional[List[MD_ScopeDescription]] = None,
                 maintenanceNote: Optional[List[str]] = None,
                 contact: Optional[List['CI_ResponsibleParty']] = None
                ):
        self.maintenanceAndUpdateFrequency = maintenanceAndUpdateFrequency
        self.dateOfNextUpdate = dateOfNextUpdate
        self.userDefinedMaintenanceFrequency = userDefinedMaintenanceFrequency
        self.updateScope = updateScope if updateScope is not None else []
        self.updateScopeDescription = updateScopeDescription if updateScopeDescription is not None else []
        self.maintenanceNote = maintenanceNote if maintenanceNote is not None else []
        self.contact = contact if contact is not None else []
    def __repr__(self) -> str:
        return f"MD_MaintenanceInformation(frequency={self.maintenanceAndUpdateFrequency})"

class MD_Usage:
    """リソースの利用法 (ISO 19115)"""
    def __init__(self,
                 specificUsage: str,
                 userDeterminedLimitations: Optional[str] = None,
                 userContactInfo: Optional[List['CI_ResponsibleParty']] = None,
                 response: Optional[str] = None
                ):
        self.specificUsage = specificUsage
        self.userDeterminedLimitations = userDeterminedLimitations
        self.userContactInfo = userContactInfo if userContactInfo is not None else []
        self.response = response
    def __repr__(self) -> str:
        return f"MD_Usage(specificUsage='{self.specificUsage}')"

class MD_MetadataScope:
    """メタデータのスコープ (ISO 19115)"""
    def __init__(self,
                 resourceScope: 'MD_ScopeCode', 
                 name: Optional[str] = None
                ):
        self.resourceScope = resourceScope
        self.name = name
    def __repr__(self) -> str:
        return f"MD_MetadataScope(resourceScope={self.resourceScope})"

class MD_Metadata:
    def __init__(self,
            # 1. メタデータ基本情報
            fileIdentifier: Optional[str] = None,
            language: Optional[str] = None, # (例: "jpn")
            characterSet: Optional[MD_CharacterSetCode] = None, # (例: MD_CharacterSetCode.UTF_8)
            parentIdentifier: Optional[str] = None, # 親メタデータ
            
            # 階層 (スコープ)
            hierarchyLevel: Optional[List[MD_ScopeCode]] = None, # (例: [MD_ScopeCode.DATASET])
            hierarchyLevelName: Optional[List[str]] = None, # 階層の自由記述名
            
            contact: Optional[List['CI_ResponsibleParty']] = None, # メタデータ作成者
            dateStamp: str = None, # メタデータ作成日 (ISO 8601 文字列)
            
            # 2. メタデータ標準
            metadataStandardName: Optional[str] = None, # (例: "ISO 19115:2003/Cor.1:2006")
            metadataStandardVersion: Optional[str] = None,
            
            # 3. リソースへの参照
            dataSetURI: Optional[List[str]] = None, # データセットへのURI

            # 4. 参照系
            spatialRepresentationInfo: Optional[List['MD_SpatialRepresentation']] = None,
            referenceSystemInfo: Optional[List['MD_ReferenceSystem']] = None,
            
            # 5. メタデータ拡張
            metadataExtensionInfo: Optional[List['MD_MetadataExtensionInformation']] = None,

            # 6. リソース本体の情報 (最重要)
            identificationInfo: Optional[List['MD_Identification']] = None, # 識別
            contentInfo: Optional[List['MD_ContentInformation']] = None, # 内容
            distributionInfo: Optional[List['MD_Distribution']] = None, # 配布
            dataQualityInfo: Optional[List['DQ_DataQuality']] = None, # 品質
            
            # 7. その他
            portrayalCatalogueInfo: Optional[List['MD_PortrayalCatalogueReference']] = None,
            metadataConstraints: Optional[List['MD_Constraints']] = None, # メタデータの制約
            applicationSchemaInfo: Optional[List['MD_ApplicationSchemaInformation']] = None,
            metadataMaintenance: Optional['MD_MaintenanceInformation'] = None, # メタデータの保守
            resourceSpecificUsage: Optional[List['MD_Usage']] = None,
            metadataScope: Optional[List['MD_MetadataScope']] = None
        ):
        
        # default_factory=list の動作を再現
        self.fileIdentifier = fileIdentifier
        self.language = language
        self.characterSet = characterSet
        self.parentIdentifier = parentIdentifier
        self.hierarchyLevel = hierarchyLevel if hierarchyLevel is not None else []
        self.hierarchyLevelName = hierarchyLevelName if hierarchyLevelName is not None else []
        self.contact = contact if contact is not None else []
        self.dateStamp = dateStamp
        self.metadataStandardName = metadataStandardName
        self.metadataStandardVersion = metadataStandardVersion
        self.dataSetURI = dataSetURI if dataSetURI is not None else []
        
        self.spatialRepresentationInfo = spatialRepresentationInfo if spatialRepresentationInfo is not None else []
        self.referenceSystemInfo = referenceSystemInfo if referenceSystemInfo is not None else []
        self.metadataExtensionInfo = metadataExtensionInfo if metadataExtensionInfo is not None else []
        
        self.identificationInfo = identificationInfo if identificationInfo is not None else []
        self.contentInfo = contentInfo if contentInfo is not None else []
        self.distributionInfo = distributionInfo if distributionInfo is not None else []
        self.dataQualityInfo = dataQualityInfo if dataQualityInfo is not None else []

        self.portrayalCatalogueInfo = portrayalCatalogueInfo if portrayalCatalogueInfo is not None else []
        self.metadataConstraints = metadataConstraints if metadataConstraints is not None else []
        self.applicationSchemaInfo = applicationSchemaInfo if applicationSchemaInfo is not None else []
        self.metadataMaintenance = metadataMaintenance
        self.resourceSpecificUsage = resourceSpecificUsage if resourceSpecificUsage is not None else []
        self.metadataScope = metadataScope if metadataScope is not None else []

    def __repr__(self) -> str:
        # (主要なフィールドのみ表示)
        parts = []
        if self.fileIdentifier: parts.append(f"fileIdentifier='{self.fileIdentifier}'")
        if self.dateStamp: parts.append(f"dateStamp='{self.dateStamp}'")
        if self.identificationInfo: parts.append(f"identificationInfo={self.identificationInfo}")
        if self.distributionInfo: parts.append(f"distributionInfo={self.distributionInfo}")
        if self.dataQualityInfo: parts.append(f"dataQualityInfo={self.dataQualityInfo}")

        return f"MD_Metadata({', '.join(parts)})"
# -----------------------------------------------------------------
# Section 6: 範囲 (Extent) 関連
# -----------------------------------------------------------------
# -----------------------------------------------------------------
# Section 6: 範囲 (Extent) 関連
# -----------------------------------------------------------------

class EX_GeographicBoundingBox:
    """
    地理的範囲 (四隅の緯度経度)
    """
    def __init__(self,
                 westBoundLongitude: float,
                 eastBoundLongitude: float,
                 southBoundLatitude: float,
                 northBoundLatitude: float
                ):
        self.westBoundLongitude = westBoundLongitude
        self.eastBoundLongitude = eastBoundLongitude
        self.southBoundLatitude = southBoundLatitude
        self.northBoundLatitude = northBoundLatitude

    def __repr__(self) -> str:
        return (f"EX_GeographicBoundingBox(W:{self.westBoundLongitude}, E:{self.eastBoundLongitude}, "
                f"S:{self.southBoundLatitude}, N:{self.northBoundLatitude})")

class TM_Object:
    """時間オブジェクトの基底 (ISO 19108)"""
    def __init__(self):
        pass # 抽象クラス

    def __repr__(self) -> str:
        return "TM_Object (Abstract)"

class TM_Primitive(TM_Object):
    """
    時間プリミティブ (簡略化)
    (TM_Object を継承)
    """
    def __init__(self,
                 value: str # 例: "2025-11-05" や "2025-01-01/2025-12-31"
                ):
        super().__init__()
        self.value = value

    def __repr__(self) -> str:
        return f"TM_Primitive(value='{self.value}')"

class EX_TemporalExtent:
    """時間的範囲"""
    def __init__(self,
                 extent: TM_Primitive
                ):
        self.extent = extent

    def __repr__(self) -> str:
        return f"EX_TemporalExtent(extent={self.extent})"

class EX_VerticalExtent:
    """(依存クラス) 垂直範囲 (ISO 19115)"""
    def __init__(self,
                 minimumValue: float,
                 maximumValue: float,
                 # (注: 垂直参照系 RS_Identifier/SC_CRS が必要)
                 verticalCRS: Optional['MD_ReferenceSystem'] = None
                ):
        self.minimumValue = minimumValue
        self.maximumValue = maximumValue
        self.verticalCRS = verticalCRS
        
    def __repr__(self) -> str:
        return f"EX_VerticalExtent(min={self.minimumValue}, max={self.maximumValue})"

class EX_Extent:
    """
    範囲 (空間的・時間的)
    """
    def __init__(self,
                 description: Optional[str] = None,
                 geographicElement: Optional[List[EX_GeographicBoundingBox]] = None,
                 temporalElement: Optional[List[EX_TemporalExtent]] = None,
                 verticalElement: Optional[List[EX_VerticalExtent]] = None
                ):
        self.description = description
        self.geographicElement = geographicElement if geographicElement is not None else []
        self.temporalElement = temporalElement if temporalElement is not None else []
        self.verticalElement = verticalElement if verticalElement is not None else []

    def __repr__(self) -> str:
        return (f"EX_Extent(description='{self.description}', "
                f"geo={len(self.geographicElement)}, temp={len(self.temporalElement)})")

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

class MD_Constraints:
    """制約の基底クラス"""
    def __init__(self,
                 useLimitation: Optional[List[str]] = None
                ):
        self.useLimitation = useLimitation if useLimitation is not None else []

    def __repr__(self) -> str:
        return f"MD_Constraints(useLimitation={self.useLimitation})"

class MD_LegalConstraints(MD_Constraints):
    """
    法的制約 (ライセンスなど)
    (MD_Constraints を継承)
    """
    def __init__(self,
                 # MD_Constraints のフィールド
                 useLimitation: Optional[List[str]] = None,
                 
                 # MD_LegalConstraints 固有のフィールド
                 accessConstraints: Optional[List[MD_RestrictionCode]] = None,
                 useConstraints: Optional[List[MD_RestrictionCode]] = None,
                 otherConstraints: Optional[List[str]] = None
                ):
        super().__init__(useLimitation=useLimitation)
        self.accessConstraints = accessConstraints if accessConstraints is not None else []
        self.useConstraints = useConstraints if useConstraints is not None else []
        self.otherConstraints = otherConstraints if otherConstraints is not None else []

    def __repr__(self) -> str:
        return f"MD_LegalConstraints(access={self.accessConstraints}, use={self.useConstraints})"

class MD_SecurityConstraints(MD_Constraints):
    """
    セキュリティ制約
    (MD_Constraints を継承)
    """
    def __init__(self,
                 # MD_Constraints のフィールド
                 useLimitation: Optional[List[str]] = None,
                 
                 # MD_SecurityConstraints 固有のフィールド
                 classification: Optional[str] = None, # (MD_ClassificationCode Enum)
                 userNote: Optional[str] = None,
                 classificationSystem: Optional[str] = None,
                 handlingDescription: Optional[str] = None
                ):
        super().__init__(useLimitation=useLimitation)
        self.classification = classification
        self.userNote = userNote
        self.classificationSystem = classificationSystem
        self.handlingDescription = handlingDescription

    def __repr__(self) -> str:
        return f"MD_SecurityConstraints(classification='{self.classification}')"

# -----------------------------------------------------------------
# Section 8: 配布 (Distribution) 関連
# -----------------------------------------------------------------

class MD_Format:
    """データ形式"""
    def __init__(self,
                 name: str, # 形式の名前 (例: "GeoTIFF")
                 version: Optional[str] = None, # バージョン (例: "1.1")
                 amendmentNumber: Optional[str] = None,
                 specification: Optional[str] = None,
                 fileDecompressionTechnique: Optional[str] = None
                ):
        self.name = name
        self.version = version
        self.amendmentNumber = amendmentNumber
        self.specification = specification
        self.fileDecompressionTechnique = fileDecompressionTechnique

    def __repr__(self) -> str:
        return f"MD_Format(name='{self.name}', version='{self.version}')"

class MD_DigitalTransferOptions:
    """デジタル転送オプション (ダウンロードURLなど)"""
    def __init__(self,
                 unitsOfDistribution: Optional[str] = None,
                 transferSize: Optional[float] = None, # (MB)
                 onLine: Optional[List['CI_OnlineResource']] = None,
                 offLine: Optional[str] = None # (MD_Medium)
                ):
        self.unitsOfDistribution = unitsOfDistribution
        self.transferSize = transferSize
        self.onLine = onLine if onLine is not None else []
        self.offLine = offLine

    def __repr__(self) -> str:
        online_count = len(self.onLine) if self.onLine else 0
        return f"MD_DigitalTransferOptions(online_links={online_count})"

class MD_DistributorContact:
    """
    (MD_Distributor が依存) 配布者の連絡先情報 (ISO 19115)
    (注: CI_ResponsibleParty とほぼ同等だが、
     distributorContactInfo のみが必須)
    """
    def __init__(self,
                 distributorContactInfo: 'CI_ResponsibleParty'
                ):
        self.distributorContactInfo = distributorContactInfo

    def __repr__(self) -> str:
        return f"MD_DistributorContact(contact={self.distributorContactInfo})"

class MD_Distributor:
    """配布者 (ISO 19115)"""
    def __init__(self,
                 distributorContact: MD_DistributorContact,
                 distributionOrderProcess: Optional[List[str]] = None # (MD_StandardOrderProcess)
                ):
        self.distributorContact = distributorContact
        self.distributionOrderProcess = distributionOrderProcess if distributionOrderProcess is not None else []

    def __repr__(self) -> str:
        return f"MD_Distributor(contact={self.distributorContact})"

class MD_Distribution:
    """配布情報"""
    def __init__(self,
                 distributionFormat: Optional[List['MD_Format']] = None,
                 transferOptions: Optional[List['MD_DigitalTransferOptions']] = None,
                 distributor: Optional[List['MD_Distributor']] = None # (依存クラス追加)
                ):
        self.distributionFormat = distributionFormat if distributionFormat is not None else []
        self.transferOptions = transferOptions if transferOptions is not None else []
        self.distributor = distributor if distributor is not None else []

    def __repr__(self) -> str:
        return f"MD_Distribution(formats={len(self.distributionFormat)}, options={len(self.transferOptions)})"

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

class MD_Resolution:
    """
    解像度 (ISO 19115)
    (注: 以前の 'value: str' という簡略化を廃止)
    """
    def __init__(self,
                 # (スケールか距離のどちらか一方を指定)
                 equivalentScale: Optional[str] = None, # (MD_RepresentativeFraction)
                 distance: Optional[float] = None # (単位: メートル)
                ):
        self.equivalentScale = equivalentScale # (例: "1:10000")
        self.distance = distance # (例: 10.0)

    def __repr__(self) -> str:
        if self.equivalentScale:
            return f"MD_Resolution(scale='{self.equivalentScale}')"
        if self.distance:
            return f"MD_Resolution(distance={self.distance}m)"
        return "MD_Resolution(empty)"

class MD_DataIdentification(MD_Identification):
    """
    データセットの具体的な識別情報
    (MD_Identification を継承)
    """
    def __init__(self,
                 # --- MD_Identification の必須フィールド ---
                 citation: 'CI_Citation',
                 abstract: str,
                 
                 # --- MD_Identification のオプショナルフィールド ---
                 pointOfContact: Optional[List['CI_ResponsibleParty']] = None,
                 descriptiveKeywords: Optional[List['MD_Keywords']] = None,
                 resourceConstraints: Optional[List[Union['MD_LegalConstraints', 'MD_SecurityConstraints', 'MD_Constraints']]] = None,
                 purpose: Optional[str] = None,
                 status: Optional[List['MD_ProgressCode']] = None,
                 graphicOverview: Optional[List[str]] = None,
                 resourceMaintenance: Optional[List['MD_MaintenanceInformation']] = None,

                 # --- MD_DataIdentification 固有のフィールド ---
                 spatialRepresentationType: Optional[List[str]] = None, # (MD_SpatialRepresentationTypeCode)
                 spatialResolution: Optional[List[MD_Resolution]] = None,
                 language: Optional[List[str]] = None, # (例: ["jpn"])
                 characterSet: Optional[List['MD_CharacterSetCode']] = None, # (例: [MD_CharacterSetCode.UTF_8])
                 topicCategory: Optional[List[str]] = None, # (MD_TopicCategoryCode)
                 environmentDescription: Optional[str] = None,
                 extent: Optional[List['EX_Extent']] = None,
                 supplementalInformation: Optional[str] = None
                ):
        
        # 親クラス(MD_Identification)の __init__ を呼び出す
        super().__init__(
            citation=citation,
            abstract=abstract,
            pointOfContact=pointOfContact,
            descriptiveKeywords=descriptiveKeywords,
            resourceConstraints=resourceConstraints,
            purpose=purpose,
            status=status,
            graphicOverview=graphicOverview,
            resourceMaintenance=resourceMaintenance
        )
        
        # 固有フィールドの初期化
        self.spatialRepresentationType = spatialRepresentationType if spatialRepresentationType is not None else []
        self.spatialResolution = spatialResolution if spatialResolution is not None else []
        self.language = language if language is not None else []
        self.characterSet = characterSet if characterSet is not None else []
        self.topicCategory = topicCategory if topicCategory is not None else []
        self.environmentDescription = environmentDescription
        self.extent = extent if extent is not None else []
        self.supplementalInformation = supplementalInformation

    def __repr__(self) -> str:
        return f"MD_DataIdentification(title='{self.citation.title}', status={self.status})"

# -----------------------------------------------------------------
# Section 10: 品質 (Data Quality) 関連
# -----------------------------------------------------------------

class LI_Source:
    """
    系譜(Lineage)におけるソースデータ (ISO 19115)
    """
    def __init__(self,
                 description: Optional[str] = None,
                 # (標準では MD_Resolution を使うが、ここではスケール分母の表現を採用)
                 scaleDenominator: Optional[str] = None, # (例: "10000")
                 sourceReferenceSystem: Optional['MD_ReferenceSystem'] = None,
                 sourceCitation: Optional['CI_Citation'] = None,
                 sourceExtent: Optional[List['EX_Extent']] = None,
                 sourceStep: Optional[List['LI_ProcessStep']] = None # (ソースが生成されたステップ)
                ):
        self.description = description
        self.scaleDenominator = scaleDenominator
        self.sourceReferenceSystem = sourceReferenceSystem
        self.sourceCitation = sourceCitation
        self.sourceExtent = sourceExtent if sourceExtent is not None else []
        self.sourceStep = sourceStep if sourceStep is not None else []

    def __repr__(self) -> str:
        title = self.sourceCitation.title if self.sourceCitation else "N/A"
        return f"LI_Source(title='{title}', scale='{self.scaleDenominator}')"

class LI_ProcessStep:
    """
    系譜(Lineage)における処理ステップ (ISO 19115)
    """
    def __init__(self,
                 description: str,
                 rationale: Optional[str] = None,
                 dateTime: Optional[str] = None, # (ISO 8601 文字列)
                 processor: Optional[List['CI_ResponsibleParty']] = None,
                 source: Optional[List['LI_Source']] = None
                ):
        self.description = description
        self.rationale = rationale
        self.dateTime = dateTime
        self.processor = processor if processor is not None else []
        self.source = source if source is not None else []

    def __repr__(self) -> str:
        return f"LI_ProcessStep(description='{self.description[:30]}...', dateTime='{self.dateTime}')"

class LI_Lineage:
    """
    系譜(Lineage)情報 (ISO 19115)
    (DQ_DataQuality が参照する未定義クラス)
    """
    def __init__(self,
                 statement: Optional[str] = None,
                 processStep: Optional[List['LI_ProcessStep']] = None,
                 source: Optional[List['LI_Source']] = None
                ):
        self.statement = statement
        self.processStep = processStep if processStep is not None else []
        self.source = source if source is not None else []

    def __repr__(self) -> str:
        steps = len(self.processStep) if self.processStep else 0
        sources = len(self.source) if self.source else 0
        return f"LI_Lineage(statement='{self.statement}', steps={steps}, sources={sources})"

class DQ_EvaluationMethodTypeCode(str, Enum):
    """品質評価の方法"""
    DIRECT = "direct" # 直接評価
    INDIRECT = "indirect" # 間接評価

    def __str__(self):
        return self.value


# -----------------------------------------------------------------
# Section 10: 品質 (Data Quality) 関連
# -----------------------------------------------------------------
class DQ_Scope:
    """品質評価の適用範囲"""
    def __init__(self,
                 level: 'MD_ScopeCode', # (MD_ScopeCode は Section 5 で定義済)
                 levelDescription: Optional[str] = None
                ):
        self.level = level
        self.levelDescription = levelDescription

    def __repr__(self) -> str:
        return f"DQ_Scope(level={self.level})"

class DQ_Result:
    """(依存クラス) 品質評価の結果 (ISO 19115)"""
    def __init__(self,
                 # (注: DQ_QuantitativeResult, DQ_ConformanceResult などの
                 #  サブクラスを持つため、ここでは主要なフィールドのみ)
                 specification: Optional['CI_Citation'] = None,
                 passResult: Optional[bool] = None,
                 dateTime: Optional[str] = None,
                 resultScope: Optional[DQ_Scope] = None
                ):
        self.specification = specification
        self.passResult = passResult
        self.dateTime = dateTime
        self.resultScope = resultScope
    
    def __repr__(self) -> str:
        return f"DQ_Result(pass={self.passResult})"

class DQ_Element:
    """
    品質要素 (基底クラス)
    """
    def __init__(self,
                 nameOfMeasure: Optional[List[str]] = None,
                 measureIdentification: Optional['MD_Identifier'] = None,
                 measureDescription: Optional[str] = None,
                 evaluationMethodType: Optional[DQ_EvaluationMethodTypeCode] = None,
                 evaluationMethodDescription: Optional[str] = None,
                 evaluationProcedure: Optional['CI_Citation'] = None,
                 dateTime: Optional[List[str]] = None,
                 result: Optional[List[DQ_Result]] = None
                ):
        self.nameOfMeasure = nameOfMeasure if nameOfMeasure is not None else []
        self.measureIdentification = measureIdentification
        self.measureDescription = measureDescription
        self.evaluationMethodType = evaluationMethodType
        self.evaluationMethodDescription = evaluationMethodDescription
        self.evaluationProcedure = evaluationProcedure
        self.dateTime = dateTime if dateTime is not None else []
        self.result = result if result is not None else []

    def __repr__(self) -> str:
        name = self.nameOfMeasure[0] if self.nameOfMeasure else "N/A"
        return f"DQ_Element(name='{name}')"

class DQ_DataQuality:
    """データ品質セクション"""
    def __init__(self,
                 scope: DQ_Scope, # 品質評価の範囲
                 report: Optional[List[DQ_Element]] = None, # 品質の報告
                 lineage: Optional['LI_Lineage'] = None # (LI_Lineage は定義済)
                ):
        self.scope = scope
        self.report = report if report is not None else []
        self.lineage = lineage

    def __repr__(self) -> str:
        reports = len(self.report) if self.report else 0
        return f"DQ_DataQuality(scope={self.scope}, reports={reports})"

class DQ_DataQuality:
    """データ品質セクション"""
    def __init__(self,
                 scope: 'DQ_Scope', # 品質評価の範囲
                 report: Optional[List['DQ_Element']] = None, # 品質の報告
                 lineage: Optional['LI_Lineage'] = None # (依存クラス追加)
                ):
        self.scope = scope
        self.report = report if report is not None else []
        self.lineage = lineage

    def __repr__(self) -> str:
        return f"DQ_DataQuality(scope={self.scope})"