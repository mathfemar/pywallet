import os
import sqlite3
import hashlib
import streamlit as st
from pathlib import Path

def init_auth_db():
    """Inicializa o banco de dados de autenticação se não existir."""
    db_path = Path("data/user_data.db")
    os.makedirs(db_path.parent, exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Criar tabela de usuários se não existir
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        is_debug BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()

def hash_password(password):
    """Cria um hash da senha usando SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def add_user(username, password, is_debug=False):
    """Adiciona um novo usuário ao banco de dados."""
    init_auth_db()
    
    try:
        conn = sqlite3.connect('data/user_data.db')
        cursor = conn.cursor()
        
        password_hash = hash_password(password)
        
        cursor.execute(
            "INSERT INTO users (username, password_hash, is_debug) VALUES (?, ?, ?)",
            (username, password_hash, is_debug)
        )
        
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        # Usuário já existe
        return False
    except Exception as e:
        st.error(f"Erro ao adicionar usuário: {str(e)}")
        return False

def check_password(username, password):
    """Verifica se a senha está correta para o usuário especificado."""
    init_auth_db()
    
    try:
        conn = sqlite3.connect('data/user_data.db')
        cursor = conn.cursor()
        
        password_hash = hash_password(password)
        
        cursor.execute(
            "SELECT * FROM users WHERE username = ? AND password_hash = ?",
            (username, password_hash)
        )
        
        user = cursor.fetchone()
        conn.close()
        
        return user is not None
    except Exception as e:
        st.error(f"Erro ao verificar senha: {str(e)}")
        return False

def create_user_if_not_exists(username, password):
    """Cria um novo usuário se não existir."""
    init_auth_db()
    
    try:
        conn = sqlite3.connect('data/user_data.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        
        if user is None:
            conn.close()
            return add_user(username, password)
        else:
            # Usuário existe, mas senha está incorreta
            conn.close()
            return False
    except Exception as e:
        st.error(f"Erro ao verificar usuário: {str(e)}")
        return False

def is_debug_user(username):
    """Verifica se o usuário é um usuário de debug."""
    init_auth_db()
    
    try:
        conn = sqlite3.connect('data/user_data.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT is_debug FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        
        conn.close()
        
        if result:
            return bool(result[0])
        return False
    except Exception as e:
        st.error(f"Erro ao verificar status de debug: {str(e)}")
        return False