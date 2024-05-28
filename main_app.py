import os
import multiprocessing

os.environ["TOKENNIZERS_PARALLELISM"] = "false"
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from uuid import uuid4
from langserve import add_routes
from router import user,chatbot

from ChatbotFIT.src.base.llm_model import get_llm_model
from ChatbotFIT.src.rag.main import build_rag_chain, InputQA, OutputQA,History_chat

model_type = "Gemini"
data_dir = "./data/"

# llm = get_llm_model(model_type=model_type)
# chatbot = build_rag_chain(llm=llm,data_dir=data_dir,data_type="pdf",model_type=model_type)
# chat_model = chatbot.get_chain()


app = FastAPI(
    title="Chatbot FIT",
    version="1.0",
    description="API for Chatbot FIT",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/")
def router():
    return {"message": "API from FIT_IUH"}

@app.get("/check")
async def check():
    return {"status": "ok"}


# @app.get("/chat_history")
# async def chat_history(input_his: History_chat):
#     chat_history = chatbot.get_session_history(input_his.session_id)
#     return {"chat_history": chat_history.messages}

# @app.post("/chat", response_model=OutputQA)
# async def chat(input_qa: InputQA):
#     answer = chat_model.invoke({"input":input_qa.question}, config={
#             "configurable": {"session_id": input_qa.session_id},
#         })
#     chatbot.save_session_history(input_qa.session_id)
#     return {"answer": answer['answer']}

# add_routes(app,chat_model, playground_type="default",path="/chat")

app.include_router(user.router)
app.include_router(chatbot.router)


if __name__ == "__main__":
    import uvicorn
    multiprocessing.freeze_support()

    uvicorn.run("main_app:app", host="0.0.0.0", port=5000,reload=True)
