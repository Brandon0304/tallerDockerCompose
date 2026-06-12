from fastapi import FastAPI, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import engine, get_db, Base
from models import Student
from schemas import StudentCreate, StudentUpdate, StudentResponse

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Student Registration API")

@app.post("/students", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
def create_student(student: StudentCreate, db: Session = Depends(get_db)):
    existing = db.query(Student).filter(Student.email == student.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    db_student = Student(**student.model_dump())
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student

@app.get("/students", response_model=list[StudentResponse])
def list_students(major: str | None = Query(None), db: Session = Depends(get_db)):
    query = db.query(Student)
    if major:
        query = query.filter(Student.major == major)
    return query.all()

@app.get("/students/majors")
def list_majors(db: Session = Depends(get_db)):
    results = db.query(Student.major).distinct().order_by(Student.major).all()
    return [m[0] for m in results]

@app.get("/students/stats")
def student_stats(db: Session = Depends(get_db)):
    total = db.query(func.count(Student.id)).scalar()
    avg_age = db.query(func.avg(Student.age)).scalar()
    majors = db.query(Student.major, func.count(Student.id).label("count")).group_by(Student.major).all()
    return {
        "total_students": total,
        "average_age": round(avg_age, 1) if avg_age else 0,
        "by_major": {m: c for m, c in majors},
    }

@app.get("/students/{student_id}", response_model=StudentResponse)
def get_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return student

@app.put("/students/{student_id}", response_model=StudentResponse)
def update_student(student_id: int, student: StudentUpdate, db: Session = Depends(get_db)):
    db_student = db.query(Student).filter(Student.id == student_id).first()
    if not db_student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    update_data = student.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_student, key, value)
    db.commit()
    db.refresh(db_student)
    return db_student

@app.delete("/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    db.delete(student)
    db.commit()
