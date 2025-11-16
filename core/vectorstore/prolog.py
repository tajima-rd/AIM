"""
Prologエンジンとの通信を担当するリポジトリ層
(pyswip が必要: pip install pyswip)
"""

import logging
from typing import List, Dict, Any
from swiplserver import PrologMQI, PrologError, SWIPNotFoundError
from metadata_repository import (
    Metadata, 
    ContentsMetadata, 
    SourceMetadata, 
    CustomClass, 
    Attribute, 
    TemporalExtentBetaDistribution, 
    TemporalExtentInstant, 
    GeoExtentDescription, 
    GeoExtentPoint, 
    GeoExtentSurface
)

logger = logging.getLogger(__name__)

class PrologRepository:
    def __init__(self, knowledge_base_file: str):
        """
        Prolog知識ベース(KB)ファイルをロードして初期化する
        """
        try:
            self.mqi = PrologMQI()
            self.prolog_thread = self.mqi.create_thread()
            
            logger.info(f"Loading knowledge base: {knowledge_base_file}")
            # 仕様書で定義した規則(inconsistent_compositionなど)と、
            # 既存の事実(has_citationの定義など)をロードする
            self.prolog_thread.consult(knowledge_base_file)
            logger.info("Prolog knowledge base loaded successfully.")
            
        except SWIPNotFoundError:
            logger.error("SWI-Prolog executable not found.")
            print("Error: SWI-Prolog (swipl) not found in PATH.")
            print("Please install SWI-Prolog.")
            raise
        except PrologError as e:
            logger.error(f"Failed to load knowledge base {knowledge_base_file}: {e}")
            raise

    def __del__(self):
        """
        クリーンアップ
        """
        if hasattr(self, 'mqi'):
            self.mqi.stop()

    def insert_facts(self, facts: List[str]) -> bool:
        """
        Prologの「事実」のリストを知識ベースにassert (挿入) する。
        例: facts = ["metadata('meta_001')", "composes_contents('meta_001', 'content_B')"]
        """
        try:
            for fact in facts:
                # 'assertz' を使って事実をKBの末尾に追加
                # fact が '.' で終わっていないことを確認
                if fact.endswith('.'):
                    fact = fact[:-1]
                
                query = f"assertz({fact})."
                logger.debug(f"Asserting fact: {query}")
                result = self.prolog_thread.query(query)
                if not result:
                    logger.warning(f"Failed to assert fact: {fact}")
                    # トランザクションを考慮する場合、ここでロールバック処理
                    return False
            logger.info(f"Successfully asserted {len(facts)} facts.")
            return True
        except PrologError as e:
            logger.error(f"Error asserting facts: {e}", exc_info=True)
            return False

    def check_composition_consistency(self) -> List[str]:
        """
        仕様書 6.1. で定義されたコンポジション制約違反をチェックする。
        (?- inconsistent_composition(X).)
        """
        try:
            logger.debug("Checking for composition inconsistencies...")
            query = "inconsistent_composition(ConflictingContentsID)."
            results = self.prolog_thread.query(query)
            
            conflicts = [r["ConflictingContentsID"] for r in results]
            if conflicts:
                logger.warning(f"Composition conflicts found: {conflicts}")
            return conflicts
        except PrologError as e:
            logger.error(f"Error checking consistency: {e}", exc_info=True)
            return ["ERROR"] # エラー発生時は矛盾ありとして扱う

    def convert_metadata_to_facts(self, meta: Metadata) -> List[str]:
        """
        PydanticのMetadataオブジェクトをPrologの「事実」のリストに変換する
        (仕様書 3, 4, 5 に基づく)
        """
        facts = []
        
        # 3.1. Metadata
        facts.append(f"metadata('{meta.id}')")
        facts.append(f"metadata_attribute('{meta.id}', id, '{meta.id}')") # fileIdentifierの代わり
        facts.append(f"metadata_attribute('{meta.id}', datastamp, '{meta.datastamp.isoformat()}')")
        facts.append(f"metadata_attribute('{meta.id}', language, '{meta.language}')")
        facts.append(f"metadata_contact('{meta.id}', '{meta.contact_id}')")

        # 3.2. SourceMetadata
        src = meta.source
        facts.append(f"sourceMetadata('{src.id}')")
        facts.append(f"aggregates_source('{meta.id}', '{src.id}')") # 関係性
        facts.append(f"has_citation('{src.id}', '{src.citation_id}')")
        facts.append(f"has_reference_system('{src.id}', '{src.reference_system_id}')")
        if src.additional_temporal_extent:
            facts.append(f"source_attribute('{src.id}', additional_temporal_extent, '{src.additional_temporal_extent}')")
        if src.additional_geographic_extent:
            facts.append(f"source_attribute('{src.id}', additional_geographic_extent, '{src.additional_geographic_extent}')")

        # 3.3. ContentsMetadata
        cont = meta.contents
        facts.append(f"contentsMetadata('{cont.id}')")
        facts.append(f"composes_contents('{meta.id}', '{cont.id}')") # 関係性
        facts.append(f"contents_attribute('{cont.id}', abstract, '{cont.abstract}')")
        facts.append(f"contents_attribute('{cont.id}', topicCategory, '{cont.topic_category}')")
        for kw_id in cont.keyword_ids:
            facts.append(f"has_keyword('{cont.id}', '{kw_id}')")

        # 4.1. GeographicExtent
        geo_extent = cont.geographic_extent
        geo_id = f"geo_{cont.id}" # ContentsIDと1:1のIDを生成
        facts.append(f"has_geographic_extent('{cont.id}', '{geo_id}')")
        
        if isinstance(geo_extent, GeoExtentDescription):
            facts.append(f"geographic_extent_is_description('{geo_id}', '{geo_extent.description}')")
        elif isinstance(geo_extent, GeoExtentPoint):
            facts.append(f"geographic_extent_is_point('{geo_id}', point('{geo_extent.lat}', '{geo_extent.lon}'))")
        elif isinstance(geo_extent, GeoExtentSurface):
            facts.append(f"geographic_extent_is_surface('{geo_id}', '{geo_extent.wkt}')")

        # 4.2. TemporalExtent
        temp_extent = cont.temporal_extent
        temp_id = f"temp_{cont.id}" # ContentsIDと1:1のIDを生成
        facts.append(f"has_temporal_extent('{cont.id}', '{temp_id}')")
        
        if isinstance(temp_extent, TemporalExtentInstant):
            facts.append(f"temporal_extent_is_instant('{temp_id}', '{temp_extent.instant.isoformat()}')")
        elif isinstance(temp_extent, TemporalExtentBetaDistribution):
            facts.append(f"temporal_extent_is_beta_distribution('{temp_id}')")
            facts.append(f"beta_dist_universe('{temp_id}', '{temp_extent.start_instant.isoformat()}', '{temp_extent.end_instant.isoformat()}')")
            facts.append(f"beta_dist_params('{temp_id}', {temp_extent.alpha}, {temp_extent.beta})")
            facts.append(f"beta_dist_description('{temp_id}', '{temp_extent.description}')")

        # 5. CustomClass (階層型EAV)
        if cont.custom_class_root:
            facts.append(f"aggregates_custom('{cont.id}', '{cont.custom_class_root.id}')")
            # _convert_custom_class_to_facts を再帰的に呼び出す
            facts.extend(self._convert_custom_class_to_facts(cont.custom_class_root))
            
        return [f.replace("'", "\\'") for f in facts] # Prologのエスケープ処理

    def _convert_custom_class_to_facts(self, cclass: CustomClass) -> List[str]:
        """
        CustomClassオブジェクトを再帰的にPrologの事実に変換する
        """
        facts = []
        facts.append(f"custom_class('{cclass.id}', '{cclass.classname}')")
        
        # 属性 (Attributes) の処理
        for attr in cclass.attributes:
            facts.append(f"attribute('{attr.id}')")
            facts.append(f"custom_class_attribute('{cclass.id}', '{attr.id}')")
            facts.append(f"attribute_value('{attr.id}', '{attr.key}', '{attr.value}', '{attr.datatype}', '{attr.description}')")
            
            # 属性の階層 (AttributeOfAttribute)
            for child_attr in attr.children:
                facts.append(f"attribute_child('{attr.id}', '{child_attr.id}')")
                # 子属性も再帰的に処理
                facts.extend(self._convert_custom_class_to_facts(CustomClass(id=f"attr_child_{child_attr.id}", classname="child_attr_wrapper", attributes=[child_attr]))) # 簡易ラッパー
        
        # クラスの階層 (ClassOfClass)
        for child_class in cclass.children:
            facts.append(f"custom_class_child('{cclass.id}', '{child_class.id}')")
            # 子クラスも再帰的に処理
            facts.extend(self._convert_custom_class_to_facts(child_class))
            
        return facts