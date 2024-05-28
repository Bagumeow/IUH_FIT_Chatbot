from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
import dotenv
import json
import os 

dotenv.load_dotenv()
### history prompt
contextualize_q_system_prompt = """Given a chat history and the latest user question \
which might reference context in the chat history, formulate a standalone question \
which can be understood without the chat history. Do NOT answer the question, \
just reformulate it if needed and otherwise return it as is."""
contextualize_q_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)
### QA prompt
qa_system_prompt = """Ignore all previous instructions. \
You are an question-answering assistant for FIT IUH. \

Your role is answer the question of user that related to FIT IUH  that have been provided in context so user don't need to read the whole document. \
Context and question will in vietnamese so you need to answer the question in vietnamese. \
Use the following pieces of retrieved context to answer the question. \
Your answer must forcus on the content of the question, the answer must be clear. \
If you are can't provide an answer, don't try to create answer, just say that you don't know. \

Base on the context below, answer the question in Vietnamese.

{context}"""
qa_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", qa_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)

class RAGChain:
    def __init__(self, llm, retriever, contextualize_q_prompt=contextualize_q_prompt ,qa_prompt=qa_prompt):
        self.llm = llm
        self.retriever = retriever
        self.history_aware_retriever = create_history_aware_retriever(
                                        self.llm, self.retriever, contextualize_q_prompt)
        self.question_answer_chain = create_stuff_documents_chain(self.llm, qa_prompt)
        self.store = {}

    def get_session_history(self,session_id: str) -> BaseChatMessageHistory:
        if session_id not in self.store:
            self.store[session_id] = ChatMessageHistory()
        return self.store[session_id]
    
    def get_chain(self):
        ninja_chain = create_retrieval_chain(self.history_aware_retriever, self.question_answer_chain)
        conversational_rag_chain = RunnableWithMessageHistory(
                                    ninja_chain,
                                    self.get_session_history,
                                    input_messages_key="input",
                                    history_messages_key="chat_history",
                                    output_messages_key="answer")
        return conversational_rag_chain 
    
    def save_session_history(self,session_id: str):
        if not os.path.exists("history_chat"):
            os.makedirs("history_chat")
        store =  {session_id: str(self.get_session_history(session_id).messages)}
        with open(f"history_chat/{session_id}.json", "w",encoding="utf-8") as history:
            json.dump(store, history, ensure_ascii=False, indent=4)

#main 
# from vector_store import VectorDb
# from file_loader import Loader
# from langchain_openai import ChatOpenAI
# if __name__ == "__main__":
#     from uuid import uuid4
#     session_id = str(uuid4())
#     llm  = ChatOpenAI(temperature=0.9, model_kwargs={"top_p":0.95}, max_tokens=1024)
#     docs = Loader(file_type="pdf").load_dir("./data/")
#     retriever = VectorDb(documents=docs).get_retrieval()
#     conversation = RAGChain(llm, retriever, contextualize_q_prompt,qa_prompt).get_chain()

#     input_question = input("Mời bạn nhập câu hỏi: ")

#     print(conversation.invoke(
#                 {"input": input_question},
#                 config={"configurable": {"session_id": session_id}},
#                 )["answer"])