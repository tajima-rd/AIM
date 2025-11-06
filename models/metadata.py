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
from ..core.database import AbstractCustomClass
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