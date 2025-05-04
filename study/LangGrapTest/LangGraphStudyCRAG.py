#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/4/27 上午9:26
@Author : zsting29@gmail.com
@File   : LangGraphStudyCRAG.py
"""
import os
from typing import TypedDict, Any

import dotenv
import weaviate
from langchain_community.tools import GoogleSerperRun
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_weaviate import WeaviateVectorStore
from langgraph.graph import StateGraph
from pydantic import BaseModel, Field
from weaviate.auth import Auth

dotenv.load_dotenv()


class GradeDocument(BaseModel):
    """文檔評分Pydantic模型"""
    binary_score: str = Field(description="文件與問題是否關聯，請回答yes或者no")


class GoogleSerperArgsSchema(BaseModel):
    query: str = Field(description="執行Google Search 查詢語句")


class GraphState(TypedDict):
    """圖結構應用程式數據狀態"""
    question: str  # 原始問題
    generation: str  # 大語言模型生成內容
    web_search: str  # 網路搜尋內容
    documents: list[Document]  # 文件列表


def format_docs(docs: list[Document]) -> str:
    """格式化傳入的文檔列表為字符串"""
    return "\n\n".join([doc.page_content for doc in docs])


# 1.create LLM
llm = ChatOpenAI(model="gpt-4o-mini")

# 2.create 檢索器
client = weaviate.connect_to_weaviate_cloud(
    cluster_url=os.getenv("WEAVIATE_URL"),
    auth_credentials=Auth.api_key(os.getenv("WEAVIATE_API_KEY"))
)
vector_store = WeaviateVectorStore(
    client=client,
    index_name="Dataset",
    text_key="text",
    embedding=OpenAIEmbeddings(model="text-embedding-3-small")
)
retriever = vector_store.as_retriever(search_type="mmr")

# create 檢索評估器
system = """你是一名評估檢索到的文件與用戶問題相關性的評估員。
如果文件包含與問題相關的關鍵字或語義，請將其評級為相關。
給出一個是否相關得分為yes或者no，以表明文件是否與問題相關。"""
grade_prompt = ChatPromptTemplate.from_messages([
    ("system", system),
    ("human", "檢索文檔：\n\n{document}\n\n用戶問題： {question}")
])
retrieval_grader = grade_prompt | llm.with_structured_output(GradeDocument)

# 4.RAG檢索加強生成
template = """你是一個問答任務的助理。使用以下檢索到的上下文來回答問題。
如果不知道就說不知道，不要胡編亂造，並保持答案簡潔。

問題: {question}
上下文: {context}
答案: """
prompt = ChatPromptTemplate.from_template(template)
rag_chain = prompt | llm.bind(temperature=0) | StrOutputParser()

# 5.網路搜尋問題重寫
system_rewrite = """你是一個將輸入問題轉換為最佳化的更好版本的問題重寫器並用於網路搜尋。
請查看輸入並嘗試推理潛在的語義意圖/含義。"""
rewrite_prompt = ChatPromptTemplate.from_messages([
    ("system", system_rewrite),
    ("human", "這裡是初始化問題:\n\n{question}\n\n請嘗試提出一個改進問題。")
])
question_rewriter = rewrite_prompt | llm.bind(temperature=0) | StrOutputParser()  # 問題重寫鏈

# 6.網路搜尋Tool
google_serper = GoogleSerperRun(
    name="google_serper",
    description=(
        "一個低成本的Google搜索API。"
        "當你需要回答有關時事的問題時，可以調用該工具。"
        "該工具的輸入是搜索查詢語句。"
    ),
    # args_schema=GoogleSerperArgsSchema,
    api_wrapper=GoogleSerperAPIWrapper(),
)


# 7. 構建圖相關節點函數
def retrieve(state: GraphState) -> Any:
    """檢索節點，根據原始問題檢索向量資料庫"""
    print("---檢索節點---")
    question = state["question"]  # 原始問題
    web_search: str  # 網路搜尋內容
    documents = retriever.invoke(question)  # 文件列表
    return {**state, "documents": documents}


def generate(state: GraphState) -> Any:
    """生成節點，根據原始問題+上下文內容調用LLM生成內容"""
    print("---LLM生成節點---")
    question = state["question"]  # 原始問題
    documents = state["documents"]  # 文件列表
    generation = rag_chain.invoke({
        "context": format_docs(documents),
        "question": question
    })  # 大語言模型生成內容
    return {**state, "generation": generation}


def grade_documents(state: GraphState) -> Any:
    """文件與原始問題關聯性評分節點"""
    print("---檢查文件與問題關聯性節點---")
    question = state["question"]  # 原始問題
    documents = state["documents"]  # 文件列表

    filtered_docs = []
    web_search = "no"
    for doc in documents:
        # 檢索評估器
        score: GradeDocument = retrieval_grader.invoke({
            "document": doc.page_content,
            "question": question
        })
        grade = score.binary_score
        if grade.lower() == "yes":
            print("---文件存在關聯---")
            filtered_docs.append(doc)
        else:
            print("---文件不存在關聯---")
            web_search = "yes"
            # continue
    return {**state, "documents": filtered_docs, "web_search": web_search}


def transform_query(state: GraphState) -> Any:
    """重寫 / 轉換查詢節點"""
    print("---重寫查詢節點---")
    question = state["question"]  # 原始問題
    better_question = question_rewriter.invoke({"question": question})
    return {**state, "question": better_question}


def web_search(state: GraphState) -> Any:
    """網路檢索節點"""
    print("---網路檢索節點---")
    question = state["question"]  # 原始問題
    documents = state["documents"]  # 文件列表

    search_content = google_serper.invoke({"query": question})
    documents.append(Document(page_content=search_content))
    return {**state, "documents": documents}


def decide_to_generate(state: GraphState) -> Any:
    """決定執行生成還是搜索節點"""
    print("---路由選擇節點---")
    web_search = state["web_search"]
    if web_search.lower() == "yes":
        print("---執行網路檢索節點---")
        return "transform_query"
    else:
        print("---LLM生成節點---")
        return "generate"


# 8.構件 圖/工作流
workflow = StateGraph(GraphState)

# 9.定義工作流節點
"""
                     |---> 精煉文檔 (LLM生成節點) -- 生成 --> 答案 
檢索節點 -> 檢索評估 ---|
              |      |---> 重新檢索 (網路檢索節點）
              |              |
              |<-------------|               
"""
workflow.add_node("retrieve", retrieve)  # 檢索節點
workflow.add_node("grade_documents", grade_documents)  # 檢查文件與問題關聯性節點
workflow.add_node("generate", generate)  # LLM生成節點
workflow.add_node("transform_query", transform_query)  # 重寫查詢節點
workflow.add_node("web_search_node", web_search)  # 網路檢索節點

# 10.定義工作流邊
workflow.set_entry_point("retrieve")  # 起點
workflow.add_edge("retrieve", "grade_documents")  # 檢索節點 相連 檢索評估節點
workflow.add_conditional_edges("grade_documents", decide_to_generate)  # 檢索評估節點 相連 條件判斷函式
workflow.add_edge("transform_query", "web_search_node")  # 重寫節點 相連  網路檢索節點
workflow.add_edge("web_search_node", "generate")  # 網路檢索節點 相連 LLM生成節點
workflow.set_finish_point("generate")  # 終點

# 11.編譯工作流
app = workflow.compile()

print(app.invoke({"question": "能介紹LLM是什麼嗎？"}))

# 清理 Weaviate 連線
client.close()
