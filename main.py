from fastapi import FastAPI, HTTPException

app = FastAPI()

tasks = [
    {"id": 1, "title": "Buy groceries", "done": False},
    {"id": 2, "title": "Finish FlyRank assignment", "done": False},
    {"id": 3, "title": "Read a book", "done": True},
]

@app.get("/")
def read_root():
    """Returns API metadata."""
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}

@app.get("/health")
def read_health():
    """Health check endpoint to verify server status."""
    return {"status": "ok"}

@app.get("/tasks")
def read_tasks():
    """Retrieve all tasks."""
    return tasks

@app.get("/tasks/{task_id}")
def read_task(task_id: int):
    """Retrieve a specific task by its ID."""
    for task in tasks:
        if task["id"] == task_id:
            return task
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

@app.post("/tasks", status_code=201)
def create_task(task_data: dict):
    """Create a new task."""
    if "title" not in task_data or not str(task_data["title"]).strip():
        raise HTTPException(status_code=400, detail="Title missing or empty")
    
    title = str(task_data["title"]).strip()
    new_id = max((t["id"] for t in tasks), default=0) + 1
    new_task = {"id": new_id, "title": title, "done": False}
    tasks.append(new_task)
    return new_task

@app.put("/tasks/{task_id}")
def update_task(task_id: int, task_data: dict):
    """Update an existing task's title or completion status."""
    if not task_data:
        raise HTTPException(status_code=400, detail="Empty body")
    
    for task in tasks:
        if task["id"] == task_id:
            if "title" in task_data:
                title = str(task_data["title"]).strip()
                if not title:
                    raise HTTPException(status_code=400, detail="Title cannot be empty")
                task["title"] = title
            if "done" in task_data:
                task["done"] = bool(task_data["done"])
            return task
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    """Delete a task by its ID."""
    for i, task in enumerate(tasks):
        if task["id"] == task_id:
            del tasks[i]
            return
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
