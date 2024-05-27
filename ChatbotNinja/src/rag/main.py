from pydantic import BaseModel, Field
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from ChatbotNinja.src.rag.file_loader import Loader
from ChatbotNinja.src.rag.rag_chain import RAGChain
from ChatbotNinja.src.rag.vector_store import VectorDb
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

def build_rag_chain(llm,data_dir,data_type):
    documents = Loader(file_type=data_type).load_dir(data_dir)

    retriever = VectorDb(model_type='Gemini',documents=documents).get_retrieval()
    rag_chain = RAGChain(llm=llm,retriever=retriever)
    return rag_chain



# if __name__ == "__main__":
#     from langchain_google_vertexai import VertexAI
#     llm = VertexAI(model_name="gemini-1.0-pro-002",streaming=True)
#     bot = Chatbot_SOP(llm=llm,data_dir="./data/",data_type="pdf")
#     bot.chat()