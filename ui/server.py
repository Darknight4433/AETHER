from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ui.state import state

app = FastAPI(title="Aether Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/status")
def get_status():
    return state

@app.post("/toggle_autonomy")
def toggle():
    state["autonomy"] = not state["autonomy"]
    return {"autonomy": state["autonomy"]}

@app.post("/toggle_dnd")
def toggle_dnd():
    state["dnd"] = not state["dnd"]
    return {"dnd": state["dnd"]}
