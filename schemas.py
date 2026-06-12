from pydantic import BaseModel, EmailStr

class StudentCreate(BaseModel):
    name: str
    email: str
    age: int
    major: str

class StudentResponse(StudentCreate):
    id: int

    class Config:
        from_attributes = True
