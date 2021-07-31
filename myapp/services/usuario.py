from myapp.config.db import get_db
import datetime
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash

def busca_usuario(username):
    query = 'SELECT * FROM user WHERE username = ?'
    db = get_db()
    resultado = db.execute(query, (username,) ).fetchone()
    return resultado

def busca_usuario_por_id(user_id):
    query = 'SELECT * FROM user WHERE id = ?' 
    resultado = get_db().execute(
            query, (user_id,)
        ).fetchone()
    return resultado
    
def cria_usuario(name, username, email, password):
    query = 'INSERT INTO user (name, username, email, password) VALUES (?, ?, ?, ?)'
    db = get_db()
    db.execute(
                query,
                (name, username, email, generate_password_hash(password))
            )
    db.commit()