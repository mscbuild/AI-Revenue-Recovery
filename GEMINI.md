# Project Context: CRM AI Agent & Dashboard (Google ADK)

## 🎯 Repository Structure
Note: This project has a specific folder nesting structure. Review the structure before changing the code:
- `/app/` — Root application module.
- `/app/app/` — **Main AI agent code (Google ADK)**. Entry point: `agent.py`.
- `/app/pages/` — Streamlit multi-page interface.
- `/data/` — Directory for storing the JSON / CSV database.
- `/tests/` — Folder with quality assessment tests (Evaluation).

## 💻 Tech Stack
- Python 3.11+ (uses the .venv virtual environment)
- Google ADK (`google-adk`) for developing the AI ​​agent.
- Streamlit for the UI (`streamlit run app/app/dashboard.py` or `streamlit run app/main.py`).
- Plotly Express for charts.

## 🛠 Instructions for the AI ​​Developer
1. **Imports**: When creating new files in `/app/pages/`, keep in mind that the root PYTHONPATH should point to the first `/app/` folder.
2. **Data Paths**: Any data files (e.g. `data.json`) should be read and written relative to the global `/data/` folder in the project root, not inside the scripts folder.
3. **Streamlit**: For Plotly charts, always use `use_container_width=True`. Wrap tables in `st.dataframe(..., use_container_width=True)`. 4. **Confidentiality**: Don't write API keys in your code. Use `os.environ` or `.env`.

## 🛑 Restrictions
- Ignore the `build/` and `*.egg-info/` folders – these are package compilation artifacts and cannot be edited.
- All agent tools (`tools`) in the internal `app/app/` folder must have strict Docstrings in English.