# AiRadioDramaCreator/core/models.py
from google.genai import types # type: ignore

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
from ..models.drama import Character


@dataclass
class WriteConfig:
    temperature: float = 0.8
    top_p: float = 0.95
    max_output_tokens: int = 8192

@dataclass
class SpeechConfig:
    temperature: float = 1.0

class SceneConfig(ABC):
    """
    あらゆる生成タスクの設定を構築するための汎用的な抽象基底クラス。
    各モダリティは独立したパラメータオブジェクトによって設定される。
    """
    def __init__(self,
                 speech_config: Optional['SpeechConfig'] = None,
                 text_config: Optional['WriteConfig'] = None,
                 scene_prompt: Optional[str] = None
                ):
        """
        Args:
            speech_config (Optional[SpeechConfig]): 音声生成用の設定オブジェクト。
            text_config (Optional[WriteConfig]): テキスト生成用の設定オブジェクト。
            scene_prompt (Optional[str]): このシーンの設定を微調整するための共通プロンプト。
        """
        self.speech_config = speech_config
        self.text_config = text_config
        self.scene_prompt = scene_prompt

        self.modalities: List[str] = []
        if self.speech_config is not None:
            self.modalities.append("audio")
        if self.text_config is not None:
            self.modalities.append("text")

        if not self.modalities:
            raise ValueError("speech_config または text_config の少なくとも一方は提供される必要があります。")

    def get_speech_config(self) -> types.GenerateContentConfig:
        """
        音声生成用のGenerateContentConfigオブジェクトを構築して返す。
        """
        if "audio" not in self.modalities:
            raise AttributeError("このシーン設定に speech_params は提供されていません。")
        return self._build_speech_config()

    def get_text_config(self) -> types.GenerateContentConfig:
        """
        テキスト生成用のGenerateContentConfigオブジェクトを構築して返す。
        """
        if "text" not in self.modalities:
            raise AttributeError("このシーン設定に text_params は提供されていません。")
        return self._build_text_config()

    @abstractmethod
    def _build_speech_config(self) -> types.GenerateContentConfig:
        """
        【サブクラスで実装】音声生成用の設定オブジェクトを具体的に構築する。
        self.speech_params と、サブクラス固有の情報（話者など）を使用する。
        """
        pass

    @abstractmethod
    def _build_text_config(self) -> types.GenerateContentConfig:
        """
        【サブクラスで実装】テキスト生成用の設定オブジェクトを具体的に構築する。
        self.text_params を使用する。
        """
        pass

class Monolog(SceneConfig):
    """
    一人語り（独白）シーンの設定を定義するクラス。
    単一話者での音声生成と、テキスト生成の設定構築ロジックを担当する。
    """
    def __init__(self,
                 speaker: Character,
                 speech_config: Optional['SpeechConfig'] = None,
                 text_config: Optional['WriteConfig'] = None,
                 scene_prompt: Optional[str] = None
                ):
        super().__init__(
            speech_config, 
            text_config, 
            scene_prompt
        )

        if not isinstance(speaker, Character):
            raise TypeError("speakerはCharacterオブジェクトである必要があります。")
        self.speaker = speaker

    def _build_speech_config(self) -> types.GenerateContentConfig:
        """
        【実装】単一話者向けの音声生成設定を構築する。
        """
        # 単一話者用のVoiceConfigオブジェクトを生成
        voice_config = types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                voice_name=self.speaker.voice.api_name
            )
        )

        # 全体のGenerateContentConfigを構築して返す
        return types.GenerateContentConfig(
            temperature=self.speech_params.temperature,
            response_modalities=["audio"],
            speech_config=types.SpeechConfig(
                voice_config=voice_config
            )
        )

    def _build_text_config(self) -> types.GenerateContentConfig:
        """
        【実装】テキスト生成設定を構築する。
        元のWriteConfigクラスが持っていたロジックをここに集約する。
        """
        # 全体のGenerateContentConfigを構築して返す
        return types.GenerateContentConfig(
            temperature=self.text_params.temperature,
            top_p=self.text_params.top_p,
            max_output_tokens=self.text_params.max_output_tokens,
            thinking_config=types.ThinkingConfig(
                thinking_budget=self.text_params.thinking_budget,
            )
        )

class Narration(SceneConfig):
    """
    ナレーションの設定を定義するクラス。
    単一話者での音声生成と、テキスト生成の設定構築ロジックを担当する。
    """
    def __init__(self,
                 speaker: Character,
                 speech_config: Optional['SpeechConfig'] = None,
                 text_config: Optional['WriteConfig'] = None,
                 scene_prompt: Optional[str] = None
                ):
        super().__init__(
            speech_config, 
            text_config, 
            scene_prompt
        )

        if not isinstance(speaker, Character):
            raise TypeError("speakerはCharacterオブジェクトである必要があります。")
        self.speaker = speaker

    def _build_speech_config(self) -> types.GenerateContentConfig:
        """
        【実装】単一話者向けの音声生成設定を構築する。
        元のSpeechConfigクラスが持っていた単一話者用のロジックをここに集約する。
        """
        # 単一話者用のVoiceConfigオブジェクトを生成
        voice_config = types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                voice_name=self.speaker.voice.api_name
            )
        )

        # 全体のGenerateContentConfigを構築して返す
        return types.GenerateContentConfig(
            temperature=self.speech_params.temperature,
            response_modalities=["audio"],
            speech_config=types.SpeechConfig(
                voice_config=voice_config
            )
        )

    def _build_text_config(self) -> types.GenerateContentConfig:
        """
        【実装】テキスト生成設定を構築する。
        元のWriteConfigクラスが持っていたロジックをここに集約する。
        """
        # 全体のGenerateContentConfigを構築して返す
        return types.GenerateContentConfig(
            temperature=self.text_params.temperature,
            top_p=self.text_params.top_p,
            max_output_tokens=self.text_params.max_output_tokens,
            thinking_config=types.ThinkingConfig(
                thinking_budget=self.text_params.thinking_budget,
            )
        )

class Dialog(SceneConfig):
    """
    二人会話シーンの設定を定義するクラス。
    2人の登場人物に特化した設定構築ロジックを担当する。
    """
    def __init__(
                self,
                character_1: Character,
                character_2: Character,
                speech_config: Optional['SpeechConfig'] = None,
                text_config: Optional['WriteConfig'] = None,
                scene_prompt: Optional[str] = None
            ):

        super().__init__(
            speech_config,
            text_config,
            scene_prompt
        )

        if not isinstance(character_1, Character):
            raise TypeError("character_1 はCharacterオブジェクトである必要があります。")
        
        if not isinstance(character_2, Character):
            raise TypeError("character_2 はCharacterオブジェクトである必要があります。")

        self.character_1 = character_1
        self.character_2 = character_2


    def _build_speech_config(self) -> types.GenerateContentConfig:
        """
        【実装】二人会話向けの音声生成設定を構築する。
        """
        characters_in_dialog = [self.character_1, self.character_2]

        speaker_config_list = [
            types.SpeakerVoiceConfig(
                speaker=char.name,
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=char.voice.api_name
                    )
                )
            ) for char in characters_in_dialog
        ]

        multi_speaker_config = types.MultiSpeakerVoiceConfig(
            speaker_voice_configs=speaker_config_list
        )
        
        return types.GenerateContentConfig(
            temperature=self.speech_params.temperature,
            response_modalities=["audio"],
            speech_config=types.SpeechConfig(
                multi_speaker_voice_config=multi_speaker_config
            )
        )

    def _build_text_config(self) -> types.GenerateContentConfig:
        return types.GenerateContentConfig(
            temperature=self.text_params.temperature,
            top_p=self.text_params.top_p,
            max_output_tokens=self.text_params.max_output_tokens,
            thinking_config=types.ThinkingConfig(
                thinking_budget=self.text_params.thinking_budget,
            )
        )

class Discussion(SceneConfig):
    """
    複数人（3人以上）の会話シーンの設定を定義するクラス。
    SceneConfigを直接継承し、複数話者の設定構築ロジックを担当する。
    """
    def __init__(
                self,
                participants: List[Character],
                speech_config: Optional['SpeechConfig'] = None,
                text_config: Optional['WriteConfig'] = None,
                scene_prompt: Optional[str] = None
            ):

        super().__init__(
            speech_config,
            text_config,
            scene_prompt
        )

        if not isinstance(participants, list) or len(participants) < 3:
            raise ValueError("Discussionのparticipantsは3人以上のCharacterを含むリストである必要があります。")
        
        # 念のため、リストの中身もチェック
        if not all(isinstance(p, Character) for p in participants):
            raise TypeError("participantsリストのすべての要素はCharacterオブジェクトである必要があります。")

        self.participants = participants

    def _build_speech_config(self) -> types.GenerateContentConfig:
        """
        【実装】複数話者向けの音声生成設定を構築する。
        このロジックはDialogクラスと実質的に同じだが、独立して実装する。
        """
        # 複数話者用のSpeakerVoiceConfigリストを生成
        speaker_config_list = [
            types.SpeakerVoiceConfig(
                speaker=char.name,
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=char.voice.api_name
                    )
                )
            ) for char in self.participants
        ]

        multi_speaker_config = types.MultiSpeakerVoiceConfig(
            speaker_voice_configs=speaker_config_list
        )
        
        # ★★★ パラメータの参照元を修正 ★★★
        return types.GenerateContentConfig(
            temperature=self.speech_params.temperature,
            response_modalities=["audio"],
            speech_config=types.SpeechConfig(
                multi_speaker_voice_config=multi_speaker_config
            )
        )

    def _build_text_config(self) -> types.GenerateContentConfig:
        """
        【実装】テキスト生成設定を構築する。
        このロジックは話者の数に依存しない。
        """
        return types.GenerateContentConfig(
            temperature=self.text_params.temperature,
            top_p=self.text_params.top_p,
            max_output_tokens=self.text_params.max_output_tokens,
            thinking_config=types.ThinkingConfig(
                thinking_budget=self.text_params.thinking_budget,
            )
        )
