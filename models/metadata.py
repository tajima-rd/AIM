from abc import ABC, abstractmethod
from pathlib import Path
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from typing import (
    List, 
    Dict, 
    Union, 
    Tuple,
    Any, 
    Literal,
    Optional
)
from ..core.class_generator import AbstractCustomClass
from iso_objects.iso19115 import CI_Contact

URI_TYPE = Literal[
    "local",     # ローカルファイルパス
    "http",      # HTTP
    "https",     # HTTPS
    "s3",        # AWS S3
    "gcs",       # Google Cloud Storage
    "ftp",       # FTP
    "unknown"    # その他・不明
]

class AddtionalAttribute:
    def __init__(
        self,
        key: str,
        value: Any,
        namespace: str = "",
        classname: str = "",
        datatype: str = "", 
        description: str = ""    
    ):
        self.namespace = namespace
        self.classname = classname
        self.key = key 
        self.value = value 
        self.datatype = datatype 
        self.description = description
    
    def __repr__(self) -> str:
        return f"AddtionalAttribute(key='{self.key}', value={self.value}, datatype='{self.datatype}')"

    def as_db_tuple(self) -> tuple:
        """
        DBに挿入するためのパラメータ順にタプルを返します。
        """
        return (
            self.namespace,
            self.classname,
            self.key,
            str(self.value), # DBのTEXT型に合わせて文字列化
            self.datatype,
            self.description
        )


class AttributeRepository:
    def __init__(
        self,
        attributes: List[AddtionalAttribute]
    ):
        self.attributes = attributes if attributes is not None else []
    
    @staticmethod
    def get_create_table_sql(
        table_name: str, 
        parent_table_name: str
    ) -> str:
        """
        Args:
            table_name (str): 
                作成する属性テーブルの名前 (例: "project_attributes")
            parent_table_name (str): 
                紐づける親テーブルの名前 (例: "projects")
        """
        
        # 親テーブル名から、汎用的な外部キーカラム名を生成 (例: "project_id")
        parent_fk_column = f"{parent_table_name.rstrip('s')}_id" 
        
        return f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id SERIAL PRIMARY KEY,
            
            {parent_fk_column} INTEGER NOT NULL,
            
            -- 属性データ
            namespace TEXT,
            classname TEXT,
            key TEXT NOT NULL,
            value TEXT,
            datatype TEXT,
            description TEXT,
            
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            
            -- 汎用的な外部キー制約
            CONSTRAINT fk_{parent_table_name}
                FOREIGN KEY({parent_fk_column}) 
                REFERENCES {parent_table_name}(id)
                ON DELETE CASCADE,
            
            -- ユニーク制約に親IDも追加
            UNIQUE({parent_fk_column}, namespace, classname, key)
        );
        """

    @staticmethod
    def get_drop_table_sql(table_name: str) -> str:
        # (引数のみ。クラスのデフォルトは使わない)
        return f"DROP TABLE IF EXISTS {table_name};"

    def get_batch_upsert_params(
        self, 
        parent_id: int,           # ★紐づける親ID (例: 5)
        table_name: str,          # ★挿入先のテーブル名 (例: "project_attributes")
        parent_table_name: str    # ★親テーブル名 (例: "projects")
    ) -> Tuple[str, List[tuple]]:
        """
        self.attributes を一括UPSERTするためのSQLとパラメータを返します。
        """
        
        # 親テーブル名から外部キーカラム名を再構築
        parent_fk_column = f"{parent_table_name.rstrip('s')}_id"

        sql = f"""
        INSERT INTO {table_name} (
            {parent_fk_column},  -- ★修正 (例: project_id)
            namespace, classname, key, value, datatype, description
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s) -- プレースホルダは7個
        ON CONFLICT ({parent_fk_column}, namespace, classname, key) DO UPDATE SET
            value = EXCLUDED.value,
            datatype = EXCLUDED.datatype,
            description = EXCLUDED.description,
            updated_at = CURRENT_TIMESTAMP;
        """
        
        params_list = []
        for attr in self.attributes:
            # 外部キーIDを先頭に追加
            params = (parent_id,) + attr.as_db_tuple()
            params_list.append(params)
        
        return sql, params_list


class Project:
    def __init__(self, 
        project_name: str = "", 
        project_description: str = "", 
        contact: CI_Contact = "", 
        root_uri: str = "",
        root_uri_type: URI_TYPE = None,
        attributes:List[AbstractCustomClass]=None,
        created_date: Optional[str] = None,
        updated_date: Optional[str] = None,
    ):
        self.project_name = project_name
        self.project_description = project_description
        self.contact = contact
        self.created_at = created_date if created_date is not None else datetime.now().isoformat()
        self.updated_at = updated_date if updated_date is not None else datetime.now().isoformat()
        self.root_uri = root_uri
        self.root_uri_type = root_uri_type
        self.attributes = attributes if attributes is not None else []

    def get_attributes(self, namaspace, classname):
        pass

    @staticmethod
    def get_create_table_sql(table_name: str = "projects") -> str:
        """
        'projects' (The "One") テーブルを作成するための
        PostgreSQL用 CREATE TABLE SQL を返します。
        """
        # contact (CI_Contact) はオブジェクトであるため、
        # JSONB 型としてシリアライズして格納するのが柔軟です。
        return f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id SERIAL PRIMARY KEY,
            project_name TEXT NOT NULL,
            project_description TEXT,
            root_uri TEXT,
            root_uri_type TEXT,
            contact JSONB,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        );
        """

    @staticmethod
    def get_updated_at_trigger_sql() -> str:
        """
        (オプション) updated_at カラムを自動更新するための
        PostgreSQLトリガー関数を作成するSQLを返します。
        
        これを一度DBで実行しておくと、
        `projects` テーブルの UPDATE 時に `updated_at` が自動で更新されます。
        """
        return """
        CREATE OR REPLACE FUNCTION trigger_set_timestamp()
        RETURNS TRIGGER AS $$
        BEGIN
          NEW.updated_at = CURRENT_TIMESTAMP;
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """

    @staticmethod
    def get_apply_trigger_sql(table_name: str = "projects") -> str:
        """
        (オプション) `get_updated_at_trigger_sql` で作成した関数を
        `projects` テーブルに適用するSQLを返します。
        """
        return f"""
        DROP TRIGGER IF EXISTS set_timestamp ON {table_name};
        CREATE TRIGGER set_timestamp
        BEFORE UPDATE ON {table_name}
        FOR EACH ROW
        EXECUTE FUNCTION trigger_set_timestamp();
        """