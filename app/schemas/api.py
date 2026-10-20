from pydantic import BaseModel, EmailStr, Field

class Register(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)

class Login(BaseModel):
    email: EmailStr
    password: str

class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=3000)

class EmailRequest(BaseModel):
    instruction: str = Field(min_length=1, max_length=3000)
    recipient_context: str = Field(default="", max_length=500)
