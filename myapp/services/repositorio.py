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
    db.commit()

def listar_repositorios_usuario(id):
    db = get_db()
    query = "select * from repository where user_id = ?"
    repositorios = db.execute( query , (id,) ).fetchall()
    return repositorios

def buscar_repositorio_por_nome(name):
    db = get_db()
    query = "select * from repository where name = ?"
    repositorio = db.execute( query , (name,) ).fetchall()
    return repositorio

def atualiza_repositorio(name, analysed):
    analysis_date = datetime.datetime.now()
    query = "UPDATE repository SET analysis_date = ?, analysed = ? WHERE name = ?"
    db = get_db()
    db.execute(
        query, (analysis_date, analysed, name)
    )
    db.commit()