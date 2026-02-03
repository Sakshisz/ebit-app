#!/bin/bash

# Start backend in background
uvicorn backend.main:app --host 0.0.0.0 --port 8000 &

# Wait for backend to be ready
sleep 5

# Start frontend
streamlit run frontend/Hovedside.py --server.port 8501 --server.address 0.0.0.0
