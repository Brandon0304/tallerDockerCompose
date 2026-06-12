from pydantic import BaseModel, EmailStr

class StudentCreate(BaseModel):
    name: str
    email: str
    age: int
    major: str

class StudentUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    age: int | None = None
    major: str | None = None

class StudentResponse(StudentCreate):
    id: int

    class Config:
        from_attributes = True
