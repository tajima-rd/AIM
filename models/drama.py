from abc import ABC, abstractmethod
from pathlib import Path
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from typing import (
    List, 
    Dict, 
    Union, 
    Any, 
    Optional
)
from ..core.class_generator import AbstractCustomClass
from ..core.config import SceneConfig

class Voice(Enum):
    """
    利用可能な話者の情報を定義する列挙型。    
    使用例:
    Voice.ACHERNAR.api_name
    """
    def __init__(
                self, 
                api_name: str, 
                description: str, 
                gender: str
            ):

        self.api_name = api_name
        self.description = description
        self.gender = gender

    # --- 話者リスト ---
    # Enumメンバー名 = (API名, 特徴, 性別)
    ACHERNAR = ("Achernar", "Soft", "F")
    ACHIRD = ("Achird", "Friendly", "M")
    ALGENIB = ("Algenib", "Gravelly", "M")
    ALGIEBA = ("Algieba", "Smooth", "M")
    ALNILAM = ("Alnilam", "Firm", "M")
    AOEDE = ("Aoede", "Breezy", "F")
    AUTONOE = ("Autonoe", "Bright", "F")
    CALLIRRHOE = ("Callirrhoe", "Easy-going", "F")
    CHARON = ("Charon", "Informative", "M")
    DESPINA = ("Despina", "Smooth", "F")
    ENCELADUS = ("Enceladus", "Breathy", "M")
    ERINOME = ("Erinome", "Clear", "F")
    FENRIR = ("Fenrir", "Excitable", "M")
    GACRUX = ("Gacrux", "Mature", "F")
    IAPETUS = ("Iapetus", "Clear", "M")
    KORE = ("Kore", "Firm", "F")
    LAOMEDEIA = ("Laomedeia", "Upbeat", "F")
    LEDA = ("Leda", "Youthful", "F")
    ORUS = ("Orus", "Firm", "M")
    PUCK = ("Puck", "Upbeat", "M")
    PULCHERRIMA = ("Pulcherrima", "Forward", "M")
    RASALGETHI = ("Rasalgethi", "Informative", "M")
    SADACHBIA = ("Sadachbia", "Lively", "M")
    SADALTAGER = ("Sadaltager", "Knowledgeable", "M")
    SCHEDAR = ("Schedar", "Even", "M")
    SULAFAT = ("Sulafat", "Warm", "F")
    UMBRIEL = ("Umbriel", "Easy-going", "M")
    VINDEMIATRIX = ("Vindemiatrix", "Gentle", "F")
    ZEPHYR = ("Zephyr", "Bright", "F")
    ZUBENELGENUBI = ("Zubenelgenubi", "Casual", "M")

    @classmethod
    def get_female_voices(cls):
        """女性の話者のみをリストで返します。"""
        return [member for member in cls if member.gender == 'F']

    @classmethod
    def get_male_voices(cls):
        """男性の話者のみをリストで返します。"""
        return [member for member in cls if member.gender == 'M']

class Character:
    def __init__(
            self,
            name: str,
            voice: Voice,
            personality: str,
            traits: List[str],
            speech_style: str,
            verbal_tics: List[str],
            background: Optional[str] = None,
            role: Optional[str] = None
        ):
        self.name: str = name
        self.voice: str = voice
        self.personality: str = personality
        self.traits: List[str] = traits
        self.speech_style: str = speech_style
        self.verbal_tics: List[str] = verbal_tics
        self.background: Optional[str] = background
        self.role: Optional[str] = role
    
    def get_character_prompt(self) -> str:
        """
        このキャラクターの属性に基づいて、AI用のプロンプト文字列を生成する。
        """
        # プロンプトの各行をリストとして構築していくと、管理がしやすい
        prompt_parts = []
        prompt_parts.append(f"### {self.name}")

        # Noneや空でない属性だけをプロンプトに追加する
        if self.personality:
            prompt_parts.append(f"- 性格: {self.personality}")
        if self.speech_style:
            prompt_parts.append(f"- 話し方: {self.speech_style}")
        if self.traits:
            prompt_parts.append(f"- 特性: {', '.join(self.traits)}")
        if self.verbal_tics:
            prompt_parts.append(f"- 口癖: {', '.join(self.verbal_tics)}")
        if self.background:
            prompt_parts.append(f"- 背景設定: {self.background}")
        if self.role:
            prompt_parts.append(f"- 役割: {self.role}")
        
        # 各行を改行で結合し、最後にキャラクター間の区切りとして空行を2つ追加する
        return "\n".join(prompt_parts) + "\n\n"

class StoryLine:
    def __init__(
            self,
            order: int,
            voice: str,
            text : str,
        ):
        self.order = order
        self.voice = voice,
        self.text = text

    def get_line(self):
        return "{self.voice}: {text}\n\n"

class Script:
    def __init__(
            self,
            lines: List[StoryLine]
        ):
        self.lines = lines

class Scene:
    order: int

    def __init__(
            self,
            scene_config: SceneConfig,
            situation: str = "",
            characters: List[Character] = None,
            place: str = "",
            scripts: List[Script] = None,
            additional_attributes = List[AbstractCustomClass]
    ):
        self.scene_config = scene_config
        self.situation = situation
        self.characters = characters
        self.place = place
        self.scripts = scripts
        self.attributes = additional_attributes

class Chapter:
    scenes:List[Scene]

    def __init__(self):
        self.scenes = list()
    
    def insert(self, scene):
        num = len(self.scenes)
        scene.order = num
        self.scenes.append(scene)

class Senario:
    def __init__(self, chapters, summary):
        self.chapters = chapters
        self.summary = summary
    
    def get_current_chapter(self):
        pass
    
    def get_previous_chapter(selfr):
        pass
    
    def get_next_chapter(self):
        pass