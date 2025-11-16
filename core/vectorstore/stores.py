"""
config.json を読み込み、複数の ChromaRepository インスタンスを
管理する「マネージャー」（ファクトリ）クラス
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

# 変更後の chroma_repository.py をインポート
from chroma import ChromaRepository

logger = logging.getLogger(__name__)

class VectorStoreManager:
    """
    config.json の "VectorStores" セクションに基づき、
    ChromaRepository のインスタンスを生成・管理する。
    """
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self._stores: Dict[str, ChromaRepository] = {}
        self._project_config: Dict = {}
        
        self._load_config()
        self._initialize_stores()

    def _load_config(self):
        """
        config.json を読み込む
        """
        logger.info(f"Loading configuration from: {self.config_path}")
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data_list = json.load(f)
                
            # JSON構造を解析して辞書に変換
            self.config = {}
            for item in config_data_list:
                self.config.update(item)

            # 必須セクションの検証
            if "Project" not in self.config:
                raise ValueError("Config JSON is missing 'Project' section.")
            if "VectorStores" not in self.config:
                raise ValueError("Config JSON is missing 'VectorStores' section.")
            
            self._project_config = self.config["Project"]
            self._vector_store_configs = self.config["VectorStores"]
            
        except FileNotFoundError:
            logger.error(f"Config file not found: {self.config_path}")
            raise
        except json.JSONDecodeError:
            logger.error(f"Failed to decode JSON from config: {self.config_path}")
            raise
        except Exception as e:
            logger.error(f"Error loading config: {e}", exc_info=True)
            raise

    def _initialize_stores(self, embedding_model_name):
        """
        "VectorStores" セクションの各定義に基づき、ChromaRepository を初期化する
        """
        logger.info(f"Initializing {len(self._vector_store_configs)} vector stores...")
        
        # プロジェクトのルートURIを取得
        project_root_uri = Path(self._project_config.get("root_uri", "."))

        for store_config in self._vector_store_configs:
            try:
                # JSON内のキーが "cllection_name" とタイプミスしているので "collection_name" も見る
                collection_name = store_config.get("collection_name") or store_config.get("cllection_name")
                if not collection_name:
                    logger.warning("Skipping store config with no 'collection_name' (or 'cllection_name').")
                    continue
                
                # 相対パスをプロジェクトルートからの絶対パスに解決
                persist_dir_relative = store_config.get("persist_directory")
                if not persist_dir_relative:
                     raise ValueError(f"'{collection_name}' is missing 'persist_directory'.")
                
                persist_directory = project_root_uri / persist_dir_relative
                
                embedding_model = store_config.get("embedding_model", embedding_model_name)

                # ChromaRepository インスタンスを生成
                repository = ChromaRepository(
                    collection_name=collection_name,
                    persist_directory=persist_directory,
                    embedding_model=embedding_model
                )
                
                # マネージャーの内部辞書に格納
                self._stores[collection_name] = repository
                logger.info(f"Successfully initialized store: '{collection_name}'")

            except Exception as e:
                logger.error(f"Failed to initialize store '{collection_name}': {e}", exc_info=True)

    def get_store(self, collection_name: str) -> Optional[ChromaRepository]:
        """
        初期化されたリポジトリインスタンスを取得する
        """
        store = self._stores.get(collection_name)
        if store is None:
            logger.error(f"Vector store '{collection_name}' not found or failed to initialize.")
        return store

    def list_stores(self) -> List[str]:
        """
        利用可能なストア名のリストを返す
        """
        return list(self._stores.keys())