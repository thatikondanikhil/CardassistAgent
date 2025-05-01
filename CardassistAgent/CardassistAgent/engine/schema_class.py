from pydantic import BaseModel,Field
from uuid import UUID


class Chat(BaseModel):
    query:str = Field(...,description="User Query")
    session_id :UUID = Field(...,description="Id of the chat session")
    
class Login(BaseModel):
    mobile_number: str = Field(...,description="User Mobile number")
    password:str=Field(...,description="Enter your password")