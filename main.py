from fastapi import FastAPI, HTTPException, Depends, Header
from sqlmodel import Session, select
from contextlib import asynccontextmanager

from models import Task, UserCredentials
from database import create_db_and_tables, get_session, engine, supabase

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


# --- Auth Routes ---

@app.post("/auth/signup", status_code=201)
def signup(creds: UserCredentials):
    if not creds.email.strip() or not creds.password.strip():
        raise HTTPException(status_code=400, detail="Email and password cannot be empty")
        
    # Send the credentials to Supabase
    response = supabase.auth.sign_up({
        "email": creds.email,
        "password": creds.password
    })
    
    return {"message": "User created successfully!", "user": response.user}


@app.post("/auth/login", status_code=200)
def login(creds: UserCredentials):
    if not creds.email.strip() or not creds.password.strip():
        raise HTTPException(status_code=400, detail="Email and password cannot be empty")
        
    try:
        # Ask Supabase to verify the password
        response = supabase.auth.sign_in_with_password({
            "email": creds.email,
            "password": creds.password
        })
        # If successful, Supabase hands us the magical JWT Access Token!
        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
            "token_type": "bearer"
        }
    except Exception as e:
        # If Supabase throws an error (e.g. wrong password), return 401
        raise HTTPException(status_code=401, detail={"error": "Invalid login credentials"})




# --- Security Guard (Dependency) ---
def verify_token(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail={"error": "Access token required"})
        
    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail={"error": "Access token required"})
        
    token = parts[1]
    
    try:
        response = supabase.auth.get_user(token)
        # We return both the user and the token (we need the token for logout later)
        return {"user": response.user, "token": token}
    except Exception:
        raise HTTPException(status_code=401, detail={"error": "Invalid or expired token"})


# --- Gate Routes (Stage 2) ---

@app.get("/public/info")
def public_info():
    return {"message": "Welcome stranger! This info is public."}

@app.get("/protected/profile")
def protected_profile(auth_data: dict = Depends(verify_token)):
    # The route ONLY runs if verify_token succeeds!
    user = auth_data["user"]
    return {
        "message": "Welcome to the VIP area!", 
        "user_email": user.email,
        "user_id": user.id
    }


@app.post("/auth/logout", status_code=204)
def logout(auth_data: dict = Depends(verify_token)):
    # Tell Supabase to destroy the session on their servers
    supabase.auth.sign_out()
    return None
