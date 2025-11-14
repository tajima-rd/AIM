import abc # 抽象基底クラスを定義するためにインポート
import sys
import json
import requests
from google.genai import types # type: ignore
from pathlib import Path
from typing import (
    List, 
    Dict, 
    Union, 
    Any, 
    Optional
)
from .rag.api_client import ApiClient
from .config import (
    Character,
    WriteConfig,
    SpeechConfig
)
from ..utils.audio_processor import AudioProcessor


# ==============================================================================
# 抽象基底生成器クラス
# ==============================================================================
class AbstractBaseGenerator(abc.ABC):
    def __init__(
            self, 
            api_client: ApiClient, 
            config: Any
        ):

        if not isinstance(api_client, ApiClient):
            raise TypeError("api_clientはApiClientのサブクラスである必要があります。")
        
        self.api_client = api_client
        self.config = config

    @abc.abstractmethod
    def generate(
            self, 
            prompt: Union[str, List[Dict[str, str]]]
        ) -> Any:
        pass

# ==============================================================================
# テキスト生成器クラス
# ==============================================================================
class TextGenerator(AbstractBaseGenerator):
    def __init__(self, api_client: ApiClient, write_config: WriteConfig):
        super().__init__(api_client, write_config)
        if not isinstance(write_config, WriteConfig):
            raise TypeError("write_configはWriteConfigのサブクラスである必要があります。")

    # このクラス独自のgenerateメソッドを新たに抽象メソッドとして定義
    @abc.abstractmethod
    def generate(self, messages: List[Dict[str, str]]) -> Optional[str]:
        pass

class GeminiTextGenerator(TextGenerator):
    """
    Google Gemini APIを使用したテキスト生成器。
    """
    def _build_gemini_config(self) -> types.GenerateContentConfig:
        return types.GenerateContentConfig(
            temperature=self.config.temperature,
            top_p=self.config.top_p,
            max_output_tokens=self.config.max_output_tokens
        )

    def generate(self, messages: List[Dict[str, str]]) -> Optional[str]:
        try:
            user_prompt = ""
            for msg in reversed(messages):
                if msg['role'] == 'user':
                    user_prompt = msg['content']
                    break
            if not user_prompt:
                raise ValueError("メッセージリストに 'user' ロールのプロンプトがありません。")

            contents = [types.Content(
                role="user",
                parts=[types.Part.from_text(text=user_prompt)]
            )]
            
            # ヘルパーメソッドを呼び出して設定を構築
            generation_config = self._build_gemini_config()

            stream = self.api_client.client.models.generate_content_stream(
                model=self.api_client.model_name,
                contents=contents,
                config=generation_config,
            )

            full_response = "".join(chunk.text for chunk in stream if chunk.text)
            return full_response.strip()

        except Exception as e:
            print(f"Gemini APIでテキスト生成中にエラーが発生しました: {e}", file=sys.stderr)
            raise

class LlamaCppTextGenerator(TextGenerator):
    def _build_llama_payload(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        return {
            "model": self.api_client.model_name,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_output_tokens,
            "stream": False
        }

    def generate(self, messages: List[Dict[str, str]]) -> Optional[str]:
        try:
            # ヘルパーメソッドを呼び出してペイロードを構築
            payload = self._build_llama_payload(messages)
            
            response = requests.post(
                self.api_client.api_url,
                headers=self.api_client.headers,
                data=json.dumps(payload),
                timeout=120
            )
            response.raise_for_status()
            response_data = response.json()
            return response_data['choices'][0]['message']['content'].strip()
        except Exception as e:
            print(f"Llama.cpp APIでエラーが発生しました: {e}", file=sys.stderr)
            raise

# ==============================================================================
# 音声生成器クラス (抽象)
# ==============================================================================
class SpeechGenerator(abc.ABC):
    def __init__(self, api_client: ApiClient, speech_config: SpeechConfig):
        self.api_client = api_client
        self.config = speech_config
        self.audio_processor = AudioProcessor()

    @abc.abstractmethod
    def generate(self, ssml_dialog: str, characters: List[Character], output_path: Path) -> Optional[Path]:
        """
        SSMLダイアログから音声を生成し、指定されたパスにMP3ファイルとして保存する。

        Args:
            ssml_dialog (str): 音声合成するSSML形式のテキスト。
            characters (List[Character]): 発話するキャラクターのリスト。
            output_path (Path): 保存先のMP3ファイルパス。

        Returns:
            Optional[Path]: 成功した場合は保存先のファイルパス、失敗した場合はNone。
        """
        pass

class GeminiSpeechGenerator(SpeechGenerator):
    """
    Google Gemini APIを使用した音声生成器。
    """
    def _build_gemini_speech_config(self, characters: List[Character]) -> types.GenerateContentConfig:
        """
        [内部メソッド] キャラクターリストからGemini用の音声設定を構築する。
        """
        num_speakers = len(characters)
        speech_config = None

        if num_speakers == 1:
            # 単一話者設定
            voice_config = types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name=characters[0].voice.api_name
                )
            )
            speech_config = types.SpeechConfig(voice_config=voice_config)
        elif num_speakers > 1:
            # 複数話者設定
            speaker_configs = [
                types.SpeakerVoiceConfig(
                    speaker=char.name,
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=char.voice.api_name
                        )
                    )
                ) for char in characters
            ]
            multi_speaker_config = types.MultiSpeakerVoiceConfig(speaker_voice_configs=speaker_configs)
            speech_config = types.SpeechConfig(multi_speaker_voice_config=multi_speaker_config)

        if speech_config is None:
            raise ValueError("音声生成には少なくとも1人のキャラクターが必要です。")

        return types.GenerateContentConfig(
            temperature=self.config.temperature,
            response_modalities=["audio"],
            speech_config=speech_config
        )

    def generate(self, ssml_dialog: str, characters: List[Character], output_path: Path) -> Optional[Path]:
        try:
            # ヘルパーメソッドでGemini用の設定を構築
            generation_config = self._build_gemini_speech_config(characters)
            
            contents = [types.Content(
                role="user",
                parts=[types.Part.from_text(text=ssml_dialog)]
            )]

            stream = self.api_client.client.models.generate_content_stream(
                model=self.api_client.model_name,
                contents=contents,
                config=generation_config,
            )

            full_audio_data = bytearray()
            final_mime_type = None
            for chunk in stream:
                if (chunk.candidates and chunk.candidates[0].content and
                        chunk.candidates[0].content.parts and chunk.candidates[0].content.parts[0].inline_data):
                    inline_data = chunk.candidates[0].content.parts[0].inline_data
                    full_audio_data.extend(inline_data.data)
                    final_mime_type = inline_data.mime_type
            
            if not full_audio_data or not final_mime_type:
                print("警告: APIから音声データが返されませんでした。")
                return None

            # AudioProcessorを使ってWAV変換とMP3保存を行う
            wav_bytes = self.audio_processor.convert_to_wav(bytes(full_audio_data), final_mime_type)
            return self.audio_processor.save_as_mp3(wav_bytes, output_path)

        except Exception as e:
            print(f"Gemini APIで音声生成中にエラーが発生しました: {e}", file=sys.stderr)
            raise

class LlamaCppSpeechGenerator(SpeechGenerator):
    """
    Llama.cppは音声生成をサポートしていません。
    """
    def generate(self, ssml_dialog: str, characters: List[Character], output_path: Path) -> Optional[Path]:
        print("警告: Llama.cppは音声生成をサポートしていません。", file=sys.stderr)
        return None

# # AiRadioDramaCreator/core/generators.py

# import mimetypes
# import struct
# from pathlib import Path
# from pydub import AudioSegment
# from google.genai import types

# from .api_client import GeminiApiClient
# from .models import (
#     SpeechConfig, 
#     WriteConfig
# )
# from .models import SceneConfig
# from .api_client import GeminiApiClient

# from typing import (
#     List, 
#     Dict, 
#     Union, 
#     Any, 
#     Optional
# )

# class Generator:
#     """
#     APIと通信し、テキストや音声などの生のデータを生成する責務を持つクラス。
#     """
#     def __init__(self, api_conn: GeminiApiClient, scene_config: SceneConfig):
#         if not isinstance(scene_config, SceneConfig):
#             raise TypeError("scene_configはSceneConfigのサブクラスである必要があります。")
        
#         self.connector = api_conn
#         self.scene_config = scene_config

#     def _prepare_contents(self, prompt: str) -> List[types.Content]:
#         return [
#             types.Content(
#                 role="user",
#                 parts=[
#                     types.Part.from_text(text=prompt),
#                 ],
#             ),
#         ]

#     def generate_text(self, prompt: str) -> Optional[str]:
#         """
#         テキストをストリーミング生成し、結合した完全な文字列を返す。
#         """
#         try:
#             config = self.scene_config.get_text_config()
#             contents = self._prepare_contents(prompt)
            
#             stream = self.connector.client.models.generate_content_stream(
#                 model=self.connector.model_name,
#                 contents=contents,
#                 config=config, # ★★★ 修正点: 'generation_config' から 'config' へ ★★★
#             )

#             full_response = "".join(chunk.text for chunk in stream if chunk.text)
#             return full_response.strip()

#         except Exception as e:
#             print(f"テキスト生成中にエラーが発生しました: {e}")
#             return None

#     def generate_audio(self, prompt: str) -> Optional[Dict[str, Union[bytes, str]]]:
#         """
#         音声をストリーミング生成し、生の音声データとMIMEタイプを返す。
#         """
#         try:
#             config = self.scene_config.get_speech_config()
#             contents = self._prepare_contents(prompt)

#             stream = self.connector.client.models.generate_content_stream(
#                 model=self.connector.model_name,
#                 contents=contents,
#                 config=config, # ★★★ 修正点: 'generation_config' から 'config' へ ★★★
#             )

#             full_audio_data = bytearray()
#             final_mime_type = None

#             for chunk in stream:
#                 if (
#                     chunk.candidates
#                     and chunk.candidates[0].content
#                     and chunk.candidates[0].content.parts
#                     and chunk.candidates[0].content.parts[0].inline_data
#                 ):
#                     inline_data = chunk.candidates[0].content.parts[0].inline_data
#                     full_audio_data.extend(inline_data.data)
#                     final_mime_type = inline_data.mime_type
            
#             if not full_audio_data or not final_mime_type:
#                 print("警告: APIから音声データが返されませんでした。")
#                 return None

#             return {"audio_data": bytes(full_audio_data), "mime_type": final_mime_type}

#         except Exception as e:
#             print(f"音声生成中にエラーが発生しました: {e}")
#             return None

# class AudioProcessor:
#     """
#     生の音声データを加工し、ファイルとして保存する責務を持つクラス。
#     このクラスのメソッドはステートレスであるため、静的メソッドとして提供する。
#     """
#     @staticmethod
#     def to_wav(raw_data: bytes, mime_type: str) -> bytes:
#         """
#         MIMEタイプ情報に基づき、生の音声データにWAVヘッダを付与する。
#         """
#         # MIMEタイプからサンプルレート等を解析
#         rate_str = mime_type.split("rate=")[-1]
#         sample_rate = int(rate_str) if rate_str.isdigit() else 24000
        
#         bits_per_sample = 16
#         num_channels = 1
#         data_size = len(raw_data)
#         bytes_per_sample = bits_per_sample // 8
#         block_align = num_channels * bytes_per_sample
#         byte_rate = sample_rate * block_align
#         chunk_size = 36 + data_size

#         header = struct.pack(
#             "<4sI4s4sIHHIIHH4sI",
#             b"RIFF", chunk_size, b"WAVE", b"fmt ",
#             16, 1, num_channels, sample_rate,
#             byte_rate, block_align, bits_per_sample,
#             b"data", data_size
#         )
#         return header + raw_data

#     @staticmethod
#     def save_as_mp3(wav_bytes: bytes, output_path: Path) -> Optional[Path]:
#         """
#         WAV形式のバイトデータをMP3ファイルとして保存する。
#         """
#         output_path.parent.mkdir(parents=True, exist_ok=True)
        
#         try:
#             # pydubはバイトデータから直接オーディオセグメントを読み込める
#             audio = AudioSegment.from_file(io.BytesIO(wav_bytes), format="wav")
#             audio.export(output_path, format="mp3")
#             print(f"MP3ファイルとして保存しました: {output_path}")
#             return output_path
#         except Exception as e:
#             print(f"MP3への変換中にエラーが発生しました: {e}")
#             return None


# class TextGenerator:
#     def __init__(
#             self, 
#             api_conn: GeminiApiClient, 
#             write_config: WriteConfig, 
#             prompt: str=None, 
#             parent=None, 
#             basename=None):
#         self.connector = api_conn
#         self.content = self._set_content(prompt)
#         self.content_config = write_config.model_config
#         self.parent = parent
#         self.basename = basename
    
#     def _set_content(self, prompt):
#         return [
#             types.Content(
#                 role="user",
#                 parts=[
#                     types.Part.from_text(text=prompt),
#                 ],
#             ),
#         ]
    
#     def generate(self):
#         """
#         ストリーミングレスポンスの全チャンクを結合して、完全なテキストを返す。
#         """
#         full_response = "" # 全てのテキストを結合するための空の文字列を準備
        
#         # ストリーミングAPIを呼び出し、全チャンクをループ処理する
#         stream = self.connector.client.models.generate_content_stream(
#             model=self.connector.model_name,
#             contents=self.content,
#             config=self.content_config,
#         )

#         for chunk in stream:
#             # chunk.textがNoneでないことを確認してから結合
#             if chunk.text:
#                 full_response += chunk.text
        
#         # 全てのループが終わった後で、結合した完全なテキストを返す
#         return full_response.strip()

# class SpeechGenerator:
#     def __init__(
#             self, 
#             api_conn: GeminiApiClient, 
#             speech_config: SpeechConfig, 
#             ssml_dialog: str, 
#             parent:Path, 
#             basename: str):
#         self.connector = api_conn
#         self.content = self._set_content(ssml_dialog)
#         self.content_config = speech_config.model_config
#         self.parent = parent
#         self.basename = basename
#         self._wav_file = None
#         self._mp3_file = None
    
#     def _set_content(self, ssml):
#         return [
#             types.Content(
#                 role="user",
#                 parts=[
#                     types.Part.from_text(text=ssml),
#                 ],
#             ),
#         ]

#     def _parse_audio_mime_type(self, mime_type: str) -> dict[str, int | None]:
#         bits_per_sample = 16
#         rate = 24000

#         # Extract rate from parameters
#         parts = mime_type.split(";")
#         for param in parts: # Skip the main type part
#             param = param.strip()
#             if param.lower().startswith("rate="):
#                 try:
#                     rate_str = param.split("=", 1)[1]
#                     rate = int(rate_str)
#                 except (ValueError, IndexError):
#                     # Handle cases like "rate=" with no value or non-integer value
#                     pass # Keep rate as default
#             elif param.startswith("audio/L"):
#                 try:
#                     bits_per_sample = int(param.split("L", 1)[1])
#                 except (ValueError, IndexError):
#                     pass # Keep bits_per_sample as default if conversion fails

#         return {"bits_per_sample": bits_per_sample, "rate": rate}
        
#     def _convert_to_wav(self, audio_data: bytes, mime_type: str) -> bytes:
#         parameters = self._parse_audio_mime_type(mime_type)
#         bits_per_sample = parameters["bits_per_sample"]
#         sample_rate = parameters["rate"]
#         num_channels = 1
#         data_size = len(audio_data)
#         bytes_per_sample = bits_per_sample // 8
#         block_align = num_channels * bytes_per_sample
#         byte_rate = sample_rate * block_align
#         chunk_size = 36 + data_size  # 36 bytes for header fields before data chunk size

#         # http://soundfile.sapp.org/doc/WaveFormat/

#         header = struct.pack(
#             "<4sI4s4sIHHIIHH4sI",
#             b"RIFF",          # ChunkID
#             chunk_size,       # ChunkSize (total file size - 8 bytes)
#             b"WAVE",          # Format
#             b"fmt ",          # Subchunk1ID
#             16,               # Subchunk1Size (16 for PCM)
#             1,                # AudioFormat (1 for PCM)
#             num_channels,     # NumChannels
#             sample_rate,      # SampleRate
#             byte_rate,        # ByteRate
#             block_align,      # BlockAlign
#             bits_per_sample,  # BitsPerSample
#             b"data",          # Subchunk2ID
#             data_size         # Subchunk2Size (size of audio data)
#         )
#         return header + audio_data

#     def _convert_to_mp3(self, wav_file: Path):
#         # 出力先のMP3ファイルパスを定義する
#         mp3_file = Path(self.parent / f"{self.basename}.mp3")

#         # ★修正点1: 入力ファイル(wav_file)の存在をチェックする
#         if not wav_file.exists():
#             print(f"Error: Input WAV file not found for MP3 conversion: {wav_file}")
#             return None

#         # 出力ディレクトリの存在を確認（これは元のコードにもあり、良いプラクティス）
#         mp3_file.parent.mkdir(parents=True, exist_ok=True)

#         print(f"Converting {wav_file.name} to MP3...")
#         try:
#             # pydubでWAVファイルを読み込む
#             audio = AudioSegment.from_file(wav_file, format=wav_file.suffix.lstrip('.'))

#             # MP3にエクスポートする
#             audio.export(mp3_file, format="mp3")

#             print(f"Successfully converted to: {mp3_file}")

#             # インスタンス変数にも保存しておく
#             self._mp3_file = mp3_file

#             return self._mp3_file

#         except FileNotFoundError:
#             print(f"Error: ffmpeg not found. Please install ffmpeg and ensure it's in your system's PATH.")
#             print("See: https://ffmpeg.org/download.html")
#             return None
#         except Exception as e:
#             print(f"An error occurred during MP3 conversion: {e}")
#             return None

#     def _save_binary_file(self, file_name, data):
#         with open(file_name, "wb") as f:
#             f.write(data)
#         print(f"File saved to: {file_name}")

#     def generate(self):
#         # Generate audio content from the dialog
#         print(f"Generating audio content for dialog.")

#         wav_file = Path(self.parent / f"{self.basename}.wav")
#         full_audio_data = bytearray()
#         final_mime_type = None

#         try:
#             # ここで音声を生成する。
#             for chunk in self.connector.client.models.generate_content_stream(
#                 model=self.connector.model_name,
#                 contents=self.content,
#                 config=self.content_config,
#             ):
#                 if (
#                     chunk.candidates
#                     and chunk.candidates[0].content
#                     and chunk.candidates[0].content.parts
#                     and chunk.candidates[0].content.parts[0].inline_data
#                     and chunk.candidates[0].content.parts[0].inline_data.data
#                 ):
#                     inline_data = chunk.candidates[0].content.parts[0].inline_data
                    
#                     # データをバッファに追加
#                     full_audio_data.extend(inline_data.data)

#                     # 最後のMIMEタイプを保持
#                     final_mime_type = inline_data.mime_type
                
#                 elif chunk.text:
#                     print(f"Text chunk: {chunk.text}")
#         except Exception as e:
#             print(f"An error occurred during audio generation: {e}")
#             raise e
        
#         if full_audio_data and final_mime_type:
#             file_extension = mimetypes.guess_extension(final_mime_type)
#             if file_extension is None:
#                 print(f"Warning: Could not guess extension for MIME type {final_mime_type}. Assuming .wav and converting.")
#                 try:
#                     # WAVに変換して保存する。
#                     wav_data = self._convert_to_wav(bytes(full_audio_data), final_mime_type)
#                     self._save_binary_file(wav_file, wav_data)
#                     self._convert_to_mp3(wav_file)

#                 except Exception as e:
#                     print(f"Error converting or saving data with MIME {final_mime_type} to WAV: {e}")
#                     return None
#             else:
#                  # その他の形式の場合（通常は発生しないが念のため）
#                  self._save_binary_file(wav_file, bytes(full_audio_data))
#         else:
#             print("No audio data was generated.")
#             return None
        
#         self._wav_file = wav_file