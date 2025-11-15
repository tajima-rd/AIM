import json
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
from .custom_class import AbstractCustomClass
from .iso_objects.iso19115 import CI_Contact



# Literal を Enum に変更
class URI_TYPE(str, Enum):
    LOCAL = "local"
    HTTP = "http"
    HTTPS = "https"
    S3 = "s3"
    GCS = "gcs"
    FTP = "ftp"
    UNKNOWN = "unknown"
    
    def __str__(self):
        return self.value

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
    
    @classmethod
    def load_from_json(cls, config_path: Path) -> "Project":
        if not config_path.exists():
            print(f"プロジェクト設定ファイルが見つかりません: {config_path}")
            raise FileNotFoundError(f"Project config file not found: {config_path}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            if not config_data or not isinstance(config_data, list) or "Project" not in config_data[0]:
                raise ValueError("JSONの形式が不正です。'Project' キーが見つかりません。")
                
            project_data_dict = config_data[0]["Project"]
                        
            # contact 辞書を CI_Contact インスタンスに変換
            contact_dict = project_data_dict.get('contact')
            if contact_dict and isinstance(contact_dict, dict):
                project_data_dict['contact'] = CI_Contact.load_from_dict(contact_dict)

            return cls(**project_data_dict)
            
        except json.JSONDecodeError as e:
            print(f"設定ファイルのJSONパースに失敗しました: {config_path} ({e})")
            raise ValueError(f"Failed to parse config file: {e}") from e
        except (IndexError, KeyError, TypeError) as e:
            print(f"JSONデータの構造が不正です: {e}")
            raise ValueError(f"Invalid JSON structure: {e}") from e
    
    def __str__(self):
        return f"<Project: {self.project_name}>"