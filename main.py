from typing import List, Optional

from fastapi import Body, Depends, FastAPI
from pydantic import BaseModel
from sqlalchemy import Boolean, Column, ForeignKey, Integer, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, relationship, sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./local_database.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    try:
        print("Trying to get the db cursor...")
        db = SessionLocal()
        yield db
    except:
        print("Database connection failed...")
    finally:
        print("Closing the connection...")
        db.close()
        print("Closed!")


class DepartmentSchema(BaseModel):
    id: Optional[int]
    name: str

    class Config:
        orm_mode = True


class StudentResponse(BaseModel):
    id: int
    name: str
    is_active: bool
    # department_id: int

    department: DepartmentSchema
    courses: list = []
    backlog_subjects: list = []

    class Config:
        orm_mode = True


class CourseResponse(BaseModel):
    id: int
    name: str
    students: list = []

    class Config:
        orm_mode = True


class StudentCourse(Base):
    """
    This is a Many to Many relatioship example
    """

    __tablename__ = "student_has_course"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    course_id = Column(Integer, ForeignKey("courses.id"))


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"))
    is_active = Column(Boolean, default=True)

    department = relationship("Department")
    backlog_subjects = relationship("Backlog")  # This is what One-To-Many relationship
    courses = relationship(
        "Course", secondary=StudentCourse.__table__, back_populates="students"
    )


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)

    students = relationship(
        "Student", secondary=StudentCourse.__table__, back_populates="courses"
    )


class Backlog(Base):
    __tablename__ = "backlogs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    subject_name = Column(Text, nullable=False)
    is_cleared = Column(Boolean, default=True)
    student_id = Column(Integer, ForeignKey("students.id"))


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)


Base.metadata.create_all(bind=engine)
app = FastAPI()


@app.get("/students", response_model=List[StudentResponse])
def get_students(db: Session = Depends(get_db)):
    return db.query(Student).all()


@app.get("/courses", response_model=List[CourseResponse])
def get_students(db: Session = Depends(get_db)):
    return db.query(Course).all()


@app.post("/students")
def create_student(input_data: dict = Body(...), db: Session = Depends(get_db)):
    print(input_data)
    student = Student(
        name=input_data["name"], department_id=input_data["department_id"]
    )
    db.add(student)
    db.commit()
    db.refresh(student)

    return student


@app.post("/courses")
def create_course(input_data: dict = Body(...), db: Session = Depends(get_db)):
    print(input_data)
    course = Course(name=input_data["name"])
    db.add(course)
    db.commit()
    db.refresh(course)

    return course


@app.post("/students/{student_id}/courses/{course_id}")
def add_course_to_student(
    student_id: int, course_id: int, db: Session = Depends(get_db)
):
    student_has_course = StudentCourse(student_id=student_id, course_id=course_id)
    db.add(student_has_course)
    db.commit()
    db.refresh(student_has_course)

    return student_has_course


@app.get("/backlogs")
def get_backlog(db: Session = Depends(get_db)):
    backlogs = db.query(Backlog).all()
    print(backlogs)
    return backlogs


@app.post("/backlogs")
def add_backlog(input_data: dict = Body(...), db: Session = Depends(get_db)):
    backlog = Backlog(
        subject_name=input_data["subject_name"], student_id=input_data["student_id"]
    )
    db.add(backlog)
    db.commit()
    db.refresh(backlog)

    return backlog


@app.get("/departments")
def get_departments(db: Session = Depends(get_db)):
    backlogs = db.query(Department).all()
    print(backlogs)
    return backlogs


@app.post("/departments")
def add_departments(input_data: dict = Body(...), db: Session = Depends(get_db)):
    dept = Department(name=input_data["name"])
    db.add(dept)
    db.commit()
    db.refresh(dept)

    return dept
