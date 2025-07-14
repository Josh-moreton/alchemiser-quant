#!/bin/bash
# Nuclear Energy Trading Dashboard Launcher

echo "🚀 Starting Nuclear Energy Trading Dashboard..."
echo "📊 Dashboard will be available at: http://localhost:8501"
echo ""

# Activate virtual environment and run streamlit
source .venv/bin/activate
streamlit run nuclear_dashboard.py --server.port 8501 --server.address localhost

echo "Dashboard stopped."
