from typing import Union
from langchain_community.vectorstores import FAISS 
# from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_google_vertexai import VertexAIEmbeddings
from langchain_openai import OpenAIEmbeddings
import dotenv
import os
dotenv.load_dotenv()
class VectorDb:
    def __init__(self,
                 model_type: str ="Gemini",
                 documents = None,
                 vector_db : Union[FAISS] = FAISS,
                 )->None:
        self.vector_db = vector_db
        if model_type == "GPT":
            self.embeddings = OpenAIEmbeddings()
            if os.path.exists("index_FIT_GPT"):
             self.db = self.vector_db.load_local("index_FIT_GPT", embeddings=self.embeddings,allow_dangerous_deserialization=True)
            else:
                self.db = self.create_vector_db(documents)
                self.db.save_local("index_FIT_GPT")
        elif model_type == "Gemini":
            self.embeddings = VertexAIEmbeddings(model_name='textembedding-gecko@latest')
            if os.path.exists("index_FIT_gemini"):
             self.db = self.vector_db.load_local("index_FIT_gemini", embeddings=self.embeddings,allow_dangerous_deserialization=True)
            else:
                self.db = self.create_vector_db(documents)
                self.db.save_local("index_FIT_gemini")
        else:
            self.embeddings = HuggingFaceEmbeddings() 

    def create_vector_db(self, documents):
        db = self.vector_db.from_documents(documents,
                                           self.embeddings)
        return db
    
    def get_retrieval(self, search_type: str = "similarity",
                      search_kwargs: dict = {"k": 5}):
        retrieval = self.db.as_retriever(search_type=search_type,
                                                search_kwargs=search_kwargs)

        return retrieval