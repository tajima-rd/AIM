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

