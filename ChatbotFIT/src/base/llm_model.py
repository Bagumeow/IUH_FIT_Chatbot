#can create GPT or Hugging face model
import torch
from transformers import BitsAndBytesConfig, AutoTokenizer, AutoModelForCausalLM, pipeline
from langchain_community.llms.huggingface_pipeline import HuggingFacePipeline
from langchain_google_vertexai import VertexAI
from typing import Union
from langchain_openai import ChatOpenAI
import dotenv

dotenv.load_dotenv()

nf4_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.bfloat16,
)

def get_llm_model(model_type: str ="Gemini", max_new_tokens = 1024,
                  **kwargs):
    if model_type == "GPT":
        llm = ChatOpenAI(temperature=0.9, model_kwargs={"top_p":0.95}, max_tokens=max_new_tokens)
        return llm
    elif model_type == "Gemini":
        llm = VertexAI(model_name="gemini-1.0-pro-002",streaming=True)
        return llm

    elif model_type == "Mistral":
        model_name = "mistralai/Mistral-7B-Instruct-v0.2"
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            # quantization_config=nf4_config,
            low_cpu_mem_usage=True,
        )
        tokenizer = AutoTokenizer.from_pretrained(model_name)

        model_pipeline = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            max_new_tokens=max_new_tokens,
            pad_token_id = tokenizer.eos_token_id,
            device_map = "auto"
        )
        llm = HuggingFacePipeline(pipeline=model_pipeline,model_kwargs = kwargs)
        return llm
    else:
        raise ValueError(f"Model type {model_type} not supported")