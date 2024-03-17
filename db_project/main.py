# main.py

from contextlib import asynccontextmanager
from typing import Union, Optional, Annotated
from db_project import settings
from sqlmodel import Field, Session, SQLModel, create_engine, select
from fastapi import FastAPI, Depends, HTTPException





class Todo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    content: str = Field(index=True)


# only needed for psycopg 3 - replace postgresql
# with postgresql+psycopg in settings.DATABASE_URL
connection_string = str(settings.DATABASE_URL).replace(
    "postgresql", "postgresql+psycopg"
)


# recycle connections after 5 minutes
# to correspond with the compute scale down
engine = create_engine(
    connection_string, connect_args={"sslmode": "require"}, pool_recycle=300
)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


# The first part of the function, before the yield, will
# be executed before the application starts.
# https://fastapi.tiangolo.com/advanced/events/#lifespan-function
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Creating tables..")
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan, title="Hello World API with DB", 
    version="0.0.1",
    servers=[
        {
            "url": "https://frequently-new-redfish.ngrok-free.app", # ADD NGROK URL Here Before Creating GPT Action
            "description": "Development Server"
        }
        ])

def get_session():
    with Session(engine) as session:
        yield session


@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/todos/", response_model=Todo)
def create_todos(todos: Todo, session: Annotated[Session, Depends(get_session)]):
        session.add(todos)
        session.commit()
        session.refresh(todos)
        return todos


@app.put("/todos/{task_id}", response_model=Todo)
def update_todo(id: int, todos: Todo):
 with Session(engine) as session:
    task = session.get(Todo, id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.content = todos.content
    session.commit()
    session.refresh(task)
    return task
 
 
@app.delete("/todos/{task_id}")
def delete_todo(task_id: int):
 with Session(engine) as session:
    task = session.get(Todo, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    session.delete(task)
    session.commit()

@app.get("/todos/", response_model=list[Todo])
def read_todos(session: Annotated[Session, Depends(get_session)]):
        todos = session.exec(select(Todo)).all()
        return todos
