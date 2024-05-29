from pydantic import BaseModel, Field
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory

from .file_loader import Loader
from .rag_chain import RAGChain
from .vector_store import VectorDb

# from file_loader import Loader
# from rag_chain import RAGChain
# from vector_store import VectorDb

import os
from uuid import uuid4
import json
import dotenv

dotenv.load_dotenv()
class InputQA(BaseModel):
    question : str = Field(..., title="Question to ask", description="The question to ask the model")
    session_id : str = Field(..., title="Session ID", description="The session ID for the chat")

class OutputQA(BaseModel):
    answer : str = Field(..., title="Answer to the question", description="The answer to the question")

class History_chat(BaseModel):
    session_id : str = Field(..., title="Session ID", description="The session ID for the chat")

def build_rag_chain(llm,data_dir,data_type,model_type="Gemini"):
    documents = Loader(file_type=data_type).load_dir(data_dir)

    retriever = VectorDb(model_type=model_type,documents=documents).get_retrieval()
    rag_chain = RAGChain(llm=llm,retriever=retriever)
    return rag_chain


# if __name__ == "__main__":
#     from langchain_google_vertexai import VertexAI
#     from langchain_openai import ChatOpenAI
#     model_type = input('Nhập loại model bạn muốn sử dụng (GPT/Gemini): ')
#     if model_type == "GPT":
#         llm = ChatOpenAI(temperature=0.9, model_kwargs={"top_p":0.95}, max_tokens=1024)
#     elif model_type == "Gemini":
#         llm = VertexAI(model_name="gemini-1.0-pro-002",streaming=True)
#     chain = build_rag_chain(llm=llm,data_dir="./data/",data_type="pdf",model_type=model_type)
#     bot = chain.get_chain()
#     input_question = input("Mời bạn nhập câu hỏi: ")

#     print(bot.invoke(
#                 {"input": input_question},
#                 config={"configurable": {"session_id": "123"}},
#                 )["answer"])