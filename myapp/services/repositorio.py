from myapp.config.db import get_db
import datetime

def listar_repositorios():
    db = get_db()
    query = "select * from repository where user_id = ?"
    repositorios = db.execute( query , (id,) ).fetchall()
    return repositorios

def criar_repositorio(name, link):
    # Conecta com o banco para inserir um novo repositorio
    db = get_db()
    query_insert = "INSERT INTO repository (name, link, user_id, creation_date, analysis_date, analysed) VALUES (?, ?, ?, ?, ?, ?)"
    db.execute(
        query_insert,(name, link, 1, datetime.datetime.now(), datetime.datetime.now(), 1),
    )