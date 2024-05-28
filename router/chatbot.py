import os
import multiprocessing

from tools.tools import *
# from tools import *
os.environ["TOKENNIZERS_PARALLELISM"] = "false"
from fastapi import FastAPI, Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from langserve import add_routes

from ChatbotFIT.src.base.llm_model import get_llm_model
from ChatbotFIT.src.rag.main import build_rag_chain, InputQA, OutputQA,History_chat

data_dir = "./data/"

llm_gpt = get_llm_model(model_type="GPT")
model_gpt = build_rag_chain(llm=llm_gpt,data_dir=data_dir,data_type="pdf",model_type="GPT")
chat_gpt = model_gpt.get_chain()

llm_gemini = get_llm_model(model_type="Gemini")
model_gemini = build_rag_chain(llm=llm_gemini,data_dir=data_dir,data_type="pdf",model_type="Gemini")
chat_gemini = model_gemini.get_chain()

router = APIRouter()


@router.get("/chatgpt/history")
async def chat_history(input_his: History_chat):
    chat_history = model_gpt.get_session_history(input_his.session_id)
    return {"chat_history": chat_history.messages}

@router.post("/chatgpt", response_model=OutputQA)
async def chat(input_qa: InputQA, access_token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    conn = create_connection()
    token_data = decode_bearer_token(access_token)
    user_id,_ = get_user(conn, token_data.email)
    print(user_id)
    if not user_id:
        raise credentials_exception
    cursor = create_cursor(conn)
    answer = chat_gpt.invoke({"input":input_qa.question}, config={
            "configurable": {"session_id": input_qa.session_id},
        })
    model_gpt.save_session_history(input_qa.session_id)

    return {"answer": answer['answer']}


@router.get("/chatgemini/history")
async def chat_history(access_token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    conn = create_connection()
    token_data = decode_bearer_token(access_token)
    user_id,_ = get_user(conn, token_data.email)
    if not user_id:
        raise credentials_exception
    
    cursor = create_cursor(conn)
    cursor.execute("SELECT * FROM history_chat WHERE user_id = %s AND model_type = %s", (user_id, "Gemini"))
    chat_history = cursor.fetchall()
    conn.close()

    return {"chat_history": chat_history}

@router.post("/chatgemini", response_model=OutputQA)
async def chat(input_qa: InputQA, access_token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    conn = create_connection()
    token_data = decode_bearer_token(access_token)
    user_id,_ = get_user(conn, token_data.email)
    # print(user_id)
    if not user_id:
        raise credentials_exception
    cursor = create_cursor(conn)
    answer = chat_gemini.invoke({"input":input_qa.question}, config={
            "configurable": {"session_id": input_qa.session_id},
        })
    
    # model_gemini.save_session_history(input_qa.session_id)
    content_qa = model_gemini.get_session_history(input_qa.session_id).messages

    # add history to db 
    #if session_id not in db then insert else update
    table_name = "history_chat"
    columns = "session_id,user_id, model_type, content"
    if not check_session_id(conn, input_qa.session_id):
        insert_query = f"INSERT INTO {table_name} ({columns}) VALUES (%s,%s, %s, %s)"
        data_insert = (input_qa.session_id, user_id, "Gemini", str(content_qa))
        cursor.execute(insert_query, data_insert)
        conn.commit()
        conn.close()
    else:
        # concat new data to content data
        update_query = f"UPDATE {table_name} SET content = CONCAT(content, %s) WHERE session_id = %s"
        data_update = ('\n' + str(content_qa), input_qa.session_id)
        cursor.execute(update_query, data_update)
        conn.commit()
        conn.close()
    return {"answer": answer['answer']}