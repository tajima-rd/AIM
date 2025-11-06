import yaml  # YAMLの整形に必要
import json
import xml.dom.minidom  # XMLの整形に必要
from typing import List, Dict, Optional, Literal, Any

# --- データ構造を定義するクラス群 (ユーザー定義をベースに) ---

class Format:
    """出力フォーマットを表現するクラス"""
    def __init__(
        self,
        schema: str,
        format_type: Literal['json', 'yaml', 'text', 'xml', 'markdown', 'unknown'] = 'unknown',
        description: Optional[str] = ""
    ):
        self.schema = schema
        self.format_type = format_type
        self.description = description

class Task:
    """プロンプト内の具体的なタスクやルールを表現するクラス"""
    def __init__(
        self,
        task_type: Literal['order', 'must', 'forbidden', 'effort', 'option'],
        items: List[str]
    ):
        self.type = task_type
        self.items = items

class InputVariable:
    """プロンプトに埋め込まれる変数を表現するクラス"""
    def __init__(
        self,
        key: str,
        key_type: Literal['direct', 'reference'],
        value: str = "",
        is_required: bool = True,
        description: str = ""
    ):
        self.key = key
        self.key_type = key_type
        self.value = value
        self.is_required = is_required
        self.description = description

class Content:
    """プロンプトの本体（タスク、入力、出力形式）を格納するクラス"""
    def __init__(
        self,
        tasks: List[Task],
        inputs: List[InputVariable],
        output_format: Optional[Format] = None
    ):
        self.tasks = tasks
        self.inputs = inputs
        self.output_format = output_format

class Prompt:
    """特定の役割（role）を持つプロンプトの構成要素をまとめるクラス"""
    def __init__(
        self,
        role: Literal['user', 'system'],
        instruction: str = "",
        content: Optional[Content] = None
    ):
        self.role = role
        self.instruction = instruction
        self.content = content

# --- 全体を管理するメインクラス ---

class PromptTemplate:
    """UserプロンプトとSystemプロンプトを管理し、相互変換を行うクラス"""
    def __init__(self, user_prompt: Prompt, system_prompt: Prompt):
        if user_prompt.role != 'user' or system_prompt.role != 'system':
            raise ValueError("user_promptとsystem_promptの役割が正しくありません。")
        self.user = user_prompt
        self.system = system_prompt

    @classmethod
    def from_yaml(cls, yaml_string: str) -> 'PromptTemplate':
        """YAML文字列からPromptTemplateオブジェクトを生成する"""
        data = yaml.safe_load(yaml_string)
        
        # --- Systemプロンプトの構築 ---
        system_data = data.get('system', {})
        system_instruction = "\n".join(system_data.get('instructions', []))
        
        system_tasks = []
        if assistant_inst := system_data.get('assistant_instructions'):
            system_tasks.append(Task('must', assistant_inst))
            
        system_prompt = Prompt(
            role='system',
            instruction=system_instruction,
            content=Content(tasks=system_tasks, inputs=[], output_format=None)
        )

        # --- Userプロンプトの構築 ---
        user_data = data.get('user', {})
        user_instruction = "\n".join(user_data.get('task', []))
        
        # Tasksの構築
        user_tasks = []
        rules = user_data.get('rules', {})
        # YAMLの'steps'をTaskの'order'にマッピング
        if steps := rules.get('steps'):
            user_tasks.append(Task(task_type='order', items=steps))
        if must_rules := rules.get('must'):
            user_tasks.append(Task(task_type='must', items=must_rules))
        if forbidden_rules := rules.get('forbidden'):
            user_tasks.append(Task(task_type='forbidden', items=forbidden_rules))
            
        # Inputsの構築
        user_inputs = []
        input_data = user_data.get('input', {})
        if must_inputs := input_data.get('must'):
            for item in must_inputs:
                user_inputs.append(InputVariable(key=item['key'], is_required=True, key_type='reference'))
        if option_inputs := input_data.get('option'):
            for item in option_inputs:
                user_inputs.append(InputVariable(key=item['key'], is_required=False, key_type='reference'))

        # Output Formatの構築
        output_format_obj = None
        if output_schema := user_data.get('output'):
            # 簡単な判定でformat_typeを決定
            format_type = 'json' if output_schema.strip().startswith('{') else 'unknown'
            output_format_obj = Format(schema=output_schema, format_type=format_type)
        
        user_content = Content(tasks=user_tasks, inputs=user_inputs, output_format=output_format_obj)
        user_prompt = Prompt(role='user', instruction=user_instruction, content=user_content)
        
        return cls(user_prompt=user_prompt, system_prompt=system_prompt)

    def to_markdown(self, role: Literal['user', 'system', 'all'] = 'all') -> str:
        """指定された役割に基づいてMarkdown形式のプロンプトを生成する"""
        parts = []
        
        # --- System部分のレンダリング ---
        if role in ['all', 'system'] and self.system.instruction:
            parts.append("### あなたへの役割（システム指示）")
            parts.append(self.system.instruction)
            parts.append("")
            
            if self.system.content and self.system.content.tasks:
                parts.append("### 出力に関するシステム指示")
                for task in self.system.content.tasks:
                    if task.type == 'must':
                        parts.extend(f"- {item}" for item in task.items)
                parts.append("")

        # --- User部分のレンダリング ---
        if role in ['all', 'user'] and self.user.instruction:
            parts.append("### 実行タスク")
            parts.append(self.user.instruction)
            parts.append("")

            if self.user.content and self.user.content.tasks:
                parts.append("### ルールと制約条件")
                parts.append("タスクを実行するにあたり、以下のルールに厳密に従ってください。")
                for task in self.user.content.tasks:
                    if task.type == 'order':
                        parts.append("\n**▼ 実行ステップ**")
                        parts.extend(f"{i}. {item}" for i, item in enumerate(task.items, 1))
                    elif task.type == 'must':
                        parts.append("\n**▼ 必ず守るべきこと**")
                        parts.extend(f"- {item}" for item in task.items)
                    elif task.type == 'forbidden':
                        parts.append("\n**▼ 禁止事項**")
                        parts.extend(f"- {item}" for item in task.items)
                parts.append("")

            if self.user.content and self.user.content.output_format:
                fmt = self.user.content.output_format
                parts.append("### 期待する出力フォーマット")
                parts.append("最終的な出力は、下記の形式に寸分違わず従ってください。")
                
                lang = fmt.format_type if fmt.format_type != 'unknown' else ''
                schema_to_show = fmt.schema  # デフォルトは元の文字列

                try:
                    if fmt.format_type == 'json':
                        # JSONを整形する
                        parsed_json = json.loads(fmt.schema)
                        schema_to_show = json.dumps(parsed_json, indent=2, ensure_ascii=False)
                    
                    elif fmt.format_type == 'yaml':
                        # YAMLを整形（正規化）する
                        parsed_yaml = yaml.safe_load(fmt.schema)
                        # sort_keys=Falseで元のキーの順序を尊重する
                        schema_to_show = yaml.dump(parsed_yaml, allow_unicode=True, default_flow_style=False, sort_keys=False)

                    elif fmt.format_type == 'xml':
                        # XMLを整形する
                        dom = xml.dom.minidom.parseString(fmt.schema)
                        pretty_xml = dom.toprettyxml(indent="  ")
                        # toprettyxmlが追加する余分な改行とXML宣言を削除
                        lines = [line for line in pretty_xml.split('\n') if line.strip()]
                        schema_to_show = '\n'.join(lines[1:] if lines and '<?xml' in lines[0] else lines)
                except (json.JSONDecodeError, TypeError):
                    parts.append(f"```\n{fmt.schema}\n```")
                
                parts.append(f"```{lang}\n{schema_to_show.strip()}\n```")

        return "\n".join(parts).strip()

