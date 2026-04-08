import os
import csv
import io
from datetime import datetime
from typing import List
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# --- DATABASE SETUP ---
# Using a relative path for the SQLite DB
DATABASE_URL = "sqlite:///./dairypro.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class EntryModel(Base):
    __tablename__ = "entries"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    kg = Column(Float)
    fat = Column(Float)
    rate = Column(Float)
    amount = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# --- SCHEMAS ---
class EntryCreate(BaseModel):
    name: str
    kg: float
    fat: float
    rate: float

class EntryResponse(BaseModel):
    id: int
    name: str
    kg: float
    fat: float
    rate: float
    amount: float
    created_at: datetime

    class Config:
        from_attributes = True

# --- APP SETUP ---
app = FastAPI(title="DairyPro API")

# Enable CORS - CRITICAL for Netlify to talk to Render
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API ROUTES ---

@app.get("/api/entries", response_model=List[EntryResponse])
def get_entries():
    db = SessionLocal()
    try:
        entries = db.query(EntryModel).order_by(EntryModel.created_at.desc()).all()
        return entries
    finally:
        db.close()

@app.post("/api/entries", response_model=EntryResponse)
def create_entry(entry: EntryCreate):
    db = SessionLocal()
    try:
        # Business logic for calculation
        amount = entry.kg * entry.fat * entry.rate
        db_entry = EntryModel(
            name=entry.name,
            kg=entry.kg,
            fat=entry.fat,
            rate=entry.rate,
            amount=amount
        )
        db.add(db_entry)
        db.commit()
        db.refresh(db_entry)
        return db_entry
    finally:
        db.close()

@app.delete("/api/entries/{entry_id}")
def delete_entry(entry_id: int):
    db = SessionLocal()
    try:
        db_entry = db.query(EntryModel).filter(EntryModel.id == entry_id).first()
        if not db_entry:
            raise HTTPException(status_code=404, detail="Entry not found")
        db.delete(db_entry)
        db.commit()
        return {"message": "Entry deleted"}
    finally:
        db.close()

@app.delete("/api/entries")
def clear_all_entries():
    db = SessionLocal()
    try:
        db.query(EntryModel).delete()
        db.commit()
        return {"message": "All entries cleared"}
    finally:
        db.close()

@app.get("/api/entries/export/csv")
def export_csv():
    db = SessionLocal()
    try:
        entries = db.query(EntryModel).all()
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Name", "Kg", "Fat %", "Rate", "Amount", "Date"])
        
        for e in entries:
            writer.writerow([
                e.id, e.name, e.kg, e.fat, e.rate, e.amount, 
                e.created_at.strftime("%Y-%m-%d %H:%M:%S")
            ])
        
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=dairy-records.csv"}
        )
    finally:
        db.close()

# --- FRONTEND SERVING ---

# Serves the index.html from your 'templates' folder
@app.get("/", response_class=HTMLResponse)
def read_root():
    template_path = os.path.join("templates", "index.html")
    if os.path.exists(template_path):
        with open(template_path, "r") as f:
            return f.read()
    return "<h1>Frontend files missing in /templates</h1>"

# Mounts the static folder for CSS/JS/Images
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)