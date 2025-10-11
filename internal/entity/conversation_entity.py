#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/9/15 下午11:30
@Author : zsting29@gmail.com
@File   : conversation_entity.py
"""
from enum import Enum

from pydantic.v1 import Field, BaseModel

# 摘要匯總模板
SUMMARIZER_TEMPLATE = """逐步總結提供的對話內容，在之前的總結基礎上繼續添加並返回一個新的總結，並確保新總結的長度不要超過2000個字元，必要的時候可以刪除一些資訊，盡可能簡潔。

EXAMPLE
當前總結:
人類詢問 AI 對人工智慧的看法。AI 認為人工智慧是一股向善的力量。

新的會話:
Human: 為什麼你認為人工智慧是一股向善的力量？
AI: 因為人工智慧將幫助人類發揮他們全部的潛力。

新的總結:
人類詢問AI對人工智慧的看法，AI認為人工智慧是一股向善的力量，因為它將幫助人類發揮全部潛力。
END OF EXAMPLE

當前總結:
{summary}

新的會話:
{new_lines}

新的總結:"""

# 會話名字提示模板
CONVERSATION_NAME_TEMPLATE = "請從用戶傳遞的內容中提取出對應的主題"


class ConversationInfo(BaseModel):
    """你需要將用戶的輸入分解為“主題”和“意圖”，以便準確識別用戶輸入的類型。
    注意：用戶的語言可能是多樣性的，可以是英文、中文、日語、法語等。
    確保你的輸出與用戶的語言盡可能一致並簡短！

    範例1：
    用戶輸入: hi, my name is LiHua.
    {
        "language_type": "用戶的輸入是純英文",
        "reasoning": "輸出語言必須是英文",
        "subject": "Users greet me"
    }

    範例2:
    用戶輸入: hello
    {
        "language_type": "用戶的輸入是純英文",
        "reasoning": "輸出語言必須是英文",
        "subject": "Greeting myself"
    }

    範例3:
    用戶輸入: www.imooc.com講了什麼
    {
        "language_type": "用戶輸入是中英文混合",
        "reasoning": "英文部分是URL，主要意圖還是使用中文表達的，所以輸出語言必須是中文",
        "subject": "詢問網站www.imooc.com"
    }

    範例4:
    用戶輸入: why小紅的年齡is老than小明?
    {
        "language_type": "用戶輸入是中英文混合",
        "reasoning": "英文部分是口語化輸入，主要意圖是中文，且中文占據更大的實際意義，所以輸出語言必須是中文",
        "subject": "詢問小紅和小明的年齡"
    }

    範例5:
    用戶輸入: yo, 你今天怎麼樣?
    {
        "language_type": "用戶輸入是中英文混合",
        "reasoning": "英文部分是口語化輸入，主要意圖是中文，所以輸出語言必須是中文",
        "subject": "詢問我今天的狀態"
    }"""
    language_type: str = Field(description="用戶輸入語言的語言類型聲明")
    reasoning: str = Field(description="對用戶輸入的文本進行語言判斷的推理過程，類型為字串")
    subject: str = Field(description=(
        "對用戶的輸入進行簡短的總結，提取輸入的“意圖”和“主題”，"
        "輸出語言必須和輸入語言保持一致，盡可能簡單明瞭，"
        "尤其是用戶問題針對模型本身時，可以透過適當的方式加入趣味性。"
    ))


# 建議問題提示詞模板
SUGGESTED_QUESTIONS_TEMPLATE = "請根據傳遞的歷史資訊預測人類最後可能會問的三個問題"


class SuggestedQuestions(BaseModel):
    """請幫我預測人類最可能會問的三個問題，並且每個問題都保持在50個字元以內。
    生成的內容必須是指定模式的JSON格式數組: ["問題1", "問題2", "問題3"]"""
    questions: list[str] = Field(description="建議問題列表，類型為字串數組")


class InvokeFrom(str, Enum):
    """會話調用來源"""
    SERVICE_API = "service_api"  # 開放api服務調用
    WEB_APP = "web_app"  # web應用
    DEBUGGER = "debugger"  # 除錯頁面
    ASSISTANT_AGENT = "assistant_agent"  # 輔助Agent調用


class MessageStatus(str, Enum):
    """會話狀態"""
    NORMAL = "normal"  # 正常
    STOP = "stop"  # 停止
    TIMEOUT = "timeout"  # 超時
    ERROR = "error"  # 出錯
