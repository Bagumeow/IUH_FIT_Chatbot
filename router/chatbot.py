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
from ChatbotFIT.src.rag.main import build_rag_chain, InputQA, OutputQA, History_chat

data_dir = "./data/"

llm_gpt = get_llm_model(model_type="GPT")
model_gpt = build_rag_chain(
    llm=llm_gpt, data_dir=data_dir, data_type="pdf", model_type="GPT"
)
chat_gpt = model_gpt.get_chain()

llm_gemini = get_llm_model(model_type="Gemini")
model_gemini = build_rag_chain(
    llm=llm_gemini, data_dir=data_dir, data_type="pdf", model_type="Gemini"
)
chat_gemini = model_gemini.get_chain()

router = APIRouter()


@router.get("/chatgemini/history")
async def chat_history(access_token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    conn = create_connection()
    token_data = decode_bearer_token(access_token)
    user_id, _ = get_user(conn, token_data.email)
    if not user_id:
        raise credentials_exception

    cursor = create_cursor(conn)
    cursor.execute(
        "SELECT session_id,content FROM history_chat WHERE user_id = %s AND model_type = %s",
        (user_id, "Gemini"),
    )
    chat_history = cursor.fetchall()
    conn.close()
    all_history = {}
    if chat_history:
        all_history = {}
        for session, content in chat_history:
            pattern = r"HumanMessage\(content='(.*?)'\)|AIMessage\(content='(.*?)'\)"

            matches = re.findall(pattern, content)
            dict_message = {}
            for i, match in enumerate(matches):
                human_content, ai_content = match
                if human_content:
                    dict_message[i] = {"human": human_content}
                elif ai_content:
                    dict_message[i] = {"ai": ai_content}

            all_history[session] = list(dict_message.values())
        return all_history

    return {"chat_history": chat_history}


@router.post("/chatgemini", response_model=OutputQA)
async def chat_gemini(input_qa: InputQA, access_token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    conn = create_connection()
    cursor = create_cursor(conn)

    token_data = decode_bearer_token(access_token)
    user_id, _ = get_user(conn, token_data.email)
    # print(user_id)
    s_historychat = load_chat_sessionid_db(cursor, input_qa.session_id)
    if s_historychat:
        list_history = parse_messages(s_historychat[0])
        history = InMemoryChatMessageHistory()
        history.add_messages(list_history)
        model_gemini.store = {input_qa.session_id: history}

    if not user_id:
        raise credentials_exception
    answer = chat_gemini.invoke(
        {"input": input_qa.question},
        config={
            "configurable": {"session_id": input_qa.session_id},
        },
    )

    # model_gemini.save_session_history(input_qa.session_id)
    content_qa = model_gemini.get_session_history(input_qa.session_id).messages

    # add history to db
    # if session_id not in db then insert else update
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
        data_update = ("\n" + str(content_qa), input_qa.session_id)
        cursor.execute(update_query, data_update)
        conn.commit()
        conn.close()
    return {"answer": answer["answer"]}


@router.get("/chatgpt/history")
async def chat_history_gpt(access_token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    conn = create_connection()
    token_data = decode_bearer_token(access_token)
    user_id, _ = get_user(conn, token_data.email)
    if not user_id:
        raise credentials_exception

    cursor = create_cursor(conn)
    cursor.execute(
        "SELECT session_id,content FROM history_chat WHERE user_id = %s AND model_type = %s",
        (user_id, "GPT"),
    )
    chat_history = cursor.fetchall()
    conn.close()
    all_history = {}
    if chat_history:
        all_history = {}
        for session, content in chat_history:
            pattern = r"HumanMessage\(content='(.*?)'\)|AIMessage\(content='(.*?)'\)"

            matches = re.findall(pattern, content)
            dict_message = {}
            for i, match in enumerate(matches):
                human_content, ai_content = match
                if human_content:
                    dict_message[i] = {"human": human_content}
                elif ai_content:
                    dict_message[i] = {"ai": ai_content}

            all_history[session] = list(dict_message.values())
        return all_history
    return {"chat_history": chat_history}


@router.post("/chatgpt", response_model=OutputQA)
async def chat_gpt(input_qa: InputQA, access_token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    conn2 = create_connection()
    token_data = decode_bearer_token(access_token)
    cursor = create_cursor(conn2)

    user_id, _ = get_user(conn2, token_data.email)
    # if this session id already exits
    s_historychat = load_chat_sessionid_db(input_qa.session_id)
    if s_historychat:
        list_history = parse_messages(s_historychat[0])
        history = InMemoryChatMessageHistory()
        history.add_messages(list_history)
        model_gpt.store = {input_qa.session_id: history}

    # print(user_id)
    if not user_id:
        raise credentials_exception

    answer = chat_gpt.invoke(
        {"input": input_qa.question},
        config={
            "configurable": {"session_id": input_qa.session_id},
        },
    )

    # model_gemini.save_session_history(input_qa.session_id)
    content_qa = model_gpt.get_session_history(input_qa.session_id).messages

    # add history to db
    # if session_id not in db then insert else update
    table_name = "history_chat"
    columns = "session_id,user_id, model_type, content"
    if not check_session_id(conn2, input_qa.session_id):
        insert_query = f"INSERT INTO {table_name} ({columns}) VALUES (%s,%s, %s, %s)"
        data_insert = (input_qa.session_id, user_id, "Gemini", str(content_qa))
        cursor.execute(insert_query, data_insert)
        conn2.commit()
        conn2.close()
    else:
        # concat new data to content data
        update_query = f"UPDATE {table_name} SET content = CONCAT(content, %s) WHERE session_id = %s"
        data_update = ("," + str(content_qa), input_qa.session_id)
        cursor.execute(update_query, data_update)
        conn2.commit()
        conn2.close()
    return {"answer": answer["answer"]}
