# FastAPI blog service
Blog api service for a [Vue3 blog page](https://github.com/HerrKKK/blog-page)

## Built with
- [Pydantic](https://docs.pydantic.dev/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy](https://sqlalchemy.org)

## Setup Project
### Create and activate Python virtual environment
Execute activate.ps1 on windows and activate.sh on linux.
```
python -m venv venv
.\venv\Script\activate.ps1
```

### Install dependency
```
pip install -r .\requirements.txt
```

### Run project
```
python ./src/main.py
```
or
```
uvicorn main:app --app-dir .\src\ --host 0.0.0.0 --port 8000
```