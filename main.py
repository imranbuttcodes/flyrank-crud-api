from fastapi import FastAPI, HTTPException, Depends
from sqlmodel import Session, select
from contextlib import asynccontextmanager

from models import Task
from database import create_db_and_tables, get_session, engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    with Session(engine) as session:
        task_count = session.exec(select(Task)).first()
        if not task_count:
            session.add(Task(title="Buy groceries", done=False))
            session.add(Task(title="Finish FlyRank assignment", done=False))
            session.add(Task(title="Read a book", done=True))
            session.commit()
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/")
def read_root():
    """Returns API metadata."""
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}

@app.get("/health")
def read_health():
    """Health check endpoint to verify server status."""
    return {"status": "ok"}

@app.get("/tasks")
def read_tasks(session: Session = Depends(get_session)):
    """Retrieve all tasks."""
    return session.exec(select(Task)).all()

@app.get("/tasks/{task_id}")
def read_task(task_id: int, session: Session = Depends(get_session)):
    """Retrieve a specific task by its ID."""
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task

@app.post("/tasks", status_code=201)
def create_task(task_data: dict, session: Session = Depends(get_session)):
    if "title" not in task_data or not task_data["title"].strip():
        raise HTTPException(status_code=400, detail="Title is required")
    
    new_task = Task(title=task_data["title"], done=task_data.get("done", False))
    session.add(new_task)
    session.commit()
    session.refresh(new_task)
    return new_task

@app.put("/tasks/{task_id}")
def update_task(task_id: int, task_data: dict, session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
    if "title" in task_data:
        task.title = task_data["title"]
    if "done" in task_data:
        task.done = task_data["done"]
        
    session.add(task)
    session.commit()
    session.refresh(task)
    return task

@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int, session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
    session.delete(task)
    session.commit()
    return None
