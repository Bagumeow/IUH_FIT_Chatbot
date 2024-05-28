import os
import warnings
import streamlit as st
from ChatbotFIT.src.base.llm_model import get_llm_model
from ChatbotFIT.src.rag.main import build_rag_chain, InputQA, OutputQA
from uuid import uuid4
from langchain_core.messages import AIMessage, HumanMessage
import asyncio
from utils import StreamlitUICallbackHandler, message_func, message_func_stream
import time
warnings.filterwarnings("ignore")

model_type = "GPT"
llm = get_llm_model(model_type=model_type)
data_dir = "./data/"

chain = build_rag_chain(llm=llm,data_dir=data_dir,data_type="pdf",model_type=model_type)
chat_bot= chain.get_chain()

st.title("FIT_Chatbot")
st.caption("ChatBot Khoa Công Nghệ thông tin - Hệ thống hỏi đáp IUH")

INITIAL_MESSAGE = [
    {
        "role": "assistant",
        "content": "Chào bạn. Tôi có thể giúp gì cho bạn?",
    },
]

loop = asyncio.new_event_loop()

# Set the event loop as the current event loop
asyncio.set_event_loop(loop)

# def reset_history():
#     for file in os.listdir("history_chat"):
#         os.remove(os.path.join("history_chat", file))
def init_new_sessionid():
    st.session_state.uuid = str(uuid4())
    return st.session_state.uuid

def get_uuid():
    if 'uuid' not in st.session_state:
        # Generate a new UUID
        st.session_state.uuid = str(uuid4())
    return st.session_state.uuid



def reset_chat():
    for key in st.session_state.keys():
        del st.session_state[key]
    st.session_state["messages"] = INITIAL_MESSAGE
    st.session_state["history"] = []
    
    # reset_history()


chat_history = []

# Add a reset button
st.sidebar.markdown("---")
if st.sidebar.button("Reset Chat"):
    reset_chat()
    session_id = init_new_sessionid()

# def get_response(input_question,session_id ):
#     return chatbot.rag_chain.invoke({"input": input_question},
#             config={
#                 "configurable": {"session_id": session_id},
#             },)

if "messages" not in st.session_state.keys():
    st.session_state["messages"] = INITIAL_MESSAGE  

if "history" not in st.session_state:
    st.session_state["history"] = []

if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})

for message in st.session_state.messages:
    message_func(
        message["content"],
        True if message["role"] == "user" else False,
        True if message["role"] == "data" else False,
    )

callback_handler = StreamlitUICallbackHandler()

def append_chat_history(question, answer):
    st.session_state["history"].append((question, answer))

def append_message(content, role="assistant", display=False):
    message = {"role": role, "content": content}
    st.session_state.messages.append(message)
    if role != "data":
        append_chat_history(st.session_state.messages[-2]["content"], content)

    if callback_handler.has_streaming_ended:
        callback_handler.has_streaming_ended = False
        return
    
import json
def save_session_history(session_id:str):
    store =  {session_id: str(st.session_state["history"])}
    with open(f"history_chat/{session_id}.json", "w",encoding="utf-8") as history:
        json.dump(store, history, ensure_ascii=False, indent=4)
        
def get_response(question,session_id:str):
    if not os.path.exists("history_chat"):
        os.makedirs("history_chat")
    placeholder_text = st.empty()
    source = ""
    output = {}
    for chunk in chat_bot.stream({"input": question},
                                                config={"configurable": {"session_id": session_id}
                                            }):
        for key in chunk:
            text = ''
            if key =="answer":
                if key not in output:
                    output[key] = chunk[key]
                else:
                    output[key] += chunk[key]
                text = chunk[key]
                # print(text, end="", flush=True)
            source += text
            placeholder_text = message_func_stream(source, placeholder_text)
            time.sleep(0.02)
    append_message(source)
    save_session_history(session_id=session_id)
    return source

session_id = get_uuid()

if __name__ == "__main__":
    if st.session_state.messages[-1]["role"] != "assistant":
        content = st.session_state.messages[-1]["content"]
        if isinstance(content,str):
            response = get_response(content,session_id)
