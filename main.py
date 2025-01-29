from pydantic import BaseModel
from ollama_service import OllamaService
from fastapi import FastAPI
import uvicorn

app = FastAPI()

class ChatMessage(BaseModel):
    buyerId: int
    supplierNumber: str
    startDate: str
    invoiceNumber: str 
    endDate: str
    message: str

ollamaService = OllamaService()

# @app.post("/init_chat")
# def do_init_chat_ollama(init: ChatMessage):
#     return ollamaService.init_chat_ollama(init.buyerId, init.supplierNumber)

@app.post("/chat")
def do_chat_ollama(message: ChatMessage):
    return ollamaService.chat_ollama(message.buyerId, message.supplierNumber, message.startDate, message.endDate, message.invoiceNumber, message.message)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
