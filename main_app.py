import os
os.environ["TOKENNIZERS_PARALLELISM"] = "false"
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from uuid import uuid4
from langserve import add_routes

from ChatbotNinja.src.base.llm_model import get_llm_model
from ChatbotNinja.src.rag.main import build_rag_chain, InputQA, OutputQA,History_chat

llm = get_llm_model(model_type="Gemini")
data_dir = "./data/"
chatbot = build_rag_chain(llm=llm,data_dir=data_dir,data_type="pdf")
chat_model = chatbot.get_chain()


app = FastAPI(
    title="Chatbot SOP",
    version="1.0",
    description="API for Chatbot SOP",
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
    return {"message": "API from NinjaSOP"}

@app.get("/check")
async def check():
    return {"status": "ok"}


@app.get("/chat_history")
async def chat_history(input_his: History_chat):
    chat_history = chatbot.get_session_history(input_his.session_id)
    return {"chat_history": chat_history.messages}

@app.post("/chat", response_model=OutputQA)
async def chat(input_qa: InputQA):
    answer = chat_model.invoke({"input":input_qa.question}, config={
            "configurable": {"session_id": input_qa.session_id},
        })
    chatbot.save_session_history(input_qa.session_id)
    return {"answer": answer['answer']}

add_routes(app,chat_model, playground_type="default",path="/chat")



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000,reload=True)
