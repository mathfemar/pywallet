import os
import pandas as pd
import numpy as np
from pathlib import Path
import streamlit as st
import re

def load_portfolio(username):
    """
    Carrega o portfólio de um usuário.
    
    Args:
        username: Nome do usuário
        
    Returns:
        DataFrame: Portfólio do usuário
    """
    file_path = Path(f"data/portfolios/{username}.csv")
    
    if file_path.exists():
        try:
            df = pd.read_csv(file_path)
            
            # Garantir que temos as colunas com nomes padrão
            if 'ticker' in df.columns:
                df['ticker'] = normalize_ticker(df['ticker'])
            
            # Converter vírgulas para pontos em valores numéricos
            numeric_columns = ['preco_medio', 'quantidade']
            for col in numeric_columns:
                if col in df.columns and df[col].dtype == 'object':
                    df[col] = df[col].astype(str).str.replace(',', '.').astype(float)
            
            # Garantir que a quantidade seja um número inteiro
            if 'quantidade' in df.columns:
                df['quantidade'] = df['quantidade'].astype(int)
            
            return df
        
        except Exception as e:
            st.error(f"Erro ao carregar o portfólio: {str(e)}")
            return pd.DataFrame(columns=['ticker', 'preco_medio', 'quantidade'])
    else:
        return pd.DataFrame(columns=['ticker', 'preco_medio', 'quantidade'])

def save_portfolio(username, portfolio_df):
    """
    Salva o portfólio de um usuário.
    
    Args:
        username: Nome do usuário
        portfolio_df: DataFrame com o portfólio
        
    Returns:
        bool: True se o salvamento foi bem-sucedido, False caso contrário
    """
    try:
        # Garantir que a pasta existe
        os.makedirs("data/portfolios", exist_ok=True)
        
        file_path = Path(f"data/portfolios/{username}.csv")
        
        # Padronizar o DataFrame antes de salvar
        df = portfolio_df.copy()
        
        # Garantir que as colunas obrigatórias existam
        required_columns = ['ticker', 'preco_medio', 'quantidade']
        if not all(col in df.columns for col in required_columns):
            missing = [col for col in required_columns if col not in df.columns]
            raise ValueError(f"Colunas obrigatórias ausentes: {', '.join(missing)}")
        
        # Normalizar tickers
        df['ticker'] = normalize_ticker(df['ticker'])
        
        # Salvar apenas as colunas necessárias
        df[required_columns].to_csv(file_path, index=False)
        
        return True
    
    except Exception as e:
        st.error(f"Erro ao salvar o portfólio: {str(e)}")
        return False

def process_imported_file(file_obj, file_type=None):
    """
    Processa um arquivo importado tentando identificar automaticamente as colunas
    
    Args:
        file_obj: Objeto de arquivo (da função st.file_uploader)
        file_type: Tipo do arquivo ('xlsx' ou 'csv'), se None será determinado pela extensão
        
    Returns:
        DataFrame: Dados processados
    """
    try:
        # Determinar tipo de arquivo pela extensão se não especificado
        if file_type is None:
            file_type = file_obj.name.split('.')[-1].lower()
        
        # Ler arquivo conforme tipo
        if file_type in ['xlsx', 'xls']:
            df = pd.read_excel(file_obj)
        else:  # csv
            # Tentar diferentes delimitadores
            for sep in [';', ',', '\t']:
                try:
                    df = pd.read_csv(file_obj, sep=sep)
                    # Se conseguir ler e tiver pelo menos 2 colunas, considera sucesso
                    if len(df.columns) >= 2:
                        break
                except:
                    # Reinicia o ponteiro do arquivo para tentar outro delimitador
                    file_obj.seek(0)
            else:
                # Se nenhum delimitador funcionou
                st.error("Não foi possível detectar o formato do arquivo CSV")
                return None
        
        # Se a importação tiver apenas 3 colunas sem cabeçalho, assume as colunas padrão
        if len(df.columns) == 3 and df.columns[0] in ['0', 0]:
            df.columns = ['ticker', 'preco_medio', 'quantidade']
        
        # Se tiver mais colunas, tentar identificar pelo conteúdo
        elif len(df.columns) >= 3:
            # Identificar coluna de ticker
            ticker_col = None
            price_col = None
            qty_col = None
            
            # Identificar coluna de ticker (procura por padrões como PETR4, VALE3)
            for col in df.columns:
                sample_values = df[col].dropna().astype(str).str.upper().tolist()[:10]
                # Se encontrar padrões de ticker em pelo menos 50% das amostras
                if sample_values and sum(1 for v in sample_values if re.match(r'^[A-Z]{4}[0-9]{1,2}$', v.strip())) >= len(sample_values)/2:
                    ticker_col = col
                    break
            
            # Identificar coluna de preço (procura por valores numéricos com vírgula ou ponto)
            for col in df.columns:
                if col == ticker_col:
                    continue
                    
                sample_values = df[col].dropna().astype(str).tolist()[:10]
                # Verificar se parece valor monetário
                if sample_values and sum(1 for v in sample_values if re.match(r'^[0-9]+[.,][0-9]{2}$', v.strip())) >= len(sample_values)/2:
                    price_col = col
                    break
            
            # Identificar coluna de quantidade (procura por valores inteiros)
            for col in df.columns:
                if col in [ticker_col, price_col]:
                    continue
                
                # Tentar converter para numérico
                try:
                    if df[col].dropna().apply(lambda x: float(str(x).replace(',', '.'))).apply(lambda x: x.is_integer()).all():
                        qty_col = col
                        break
                except:
                    continue
            
            # Se identificou todas as colunas, renomear
            if ticker_col and price_col and qty_col:
                column_mapping = {
                    ticker_col: 'ticker',
                    price_col: 'preco_medio', 
                    qty_col: 'quantidade'
                }
                df = df.rename(columns=column_mapping)
                df = df[['ticker', 'preco_medio', 'quantidade']]
            else:
                # Se não conseguiu identificar automaticamente, pegar as três primeiras colunas
                if len(df.columns) >= 3:
                    new_columns = list(df.columns)
                    column_mapping = {
                        new_columns[0]: 'ticker',
                        new_columns[1]: 'preco_medio',
                        new_columns[2]: 'quantidade'
                    }
                    df = df.rename(columns=column_mapping)
                    df = df[['ticker', 'preco_medio', 'quantidade']]
                else:
                    st.error("Formato do arquivo não reconhecido. Use um arquivo com 3 colunas: Código do ativo, Preço Médio e Quantidade.")
                    return None
        
        # Normalizar dados
        
        # 1. Ticker: padronizar para maiúsculo
        df['ticker'] = normalize_ticker(df['ticker'])
        
        # 2. Preço médio: converter vírgulas para pontos
        if df['preco_medio'].dtype == 'object':
            df['preco_medio'] = df['preco_medio'].astype(str).str.replace(',', '.').astype(float)
        
        # 3. Quantidade: garantir que é inteiro
        df['quantidade'] = df['quantidade'].astype(str).str.replace(',', '.').astype(float).astype(int)
        
        return df
    
    except Exception as e:
        st.error(f"Erro ao processar arquivo: {str(e)}")
        return None

def normalize_ticker(ticker_series):
    """
    Normaliza os códigos de ações para o formato padrão.
    
    Args:
        ticker_series: Série de tickers
        
    Returns:
        Series: Série normalizada
    """
    if isinstance(ticker_series, pd.Series):
        return ticker_series.astype(str).str.upper().str.strip()
    elif isinstance(ticker_series, str):
        return ticker_series.upper().strip()
    else:
        return ticker_series

def format_currency_br(value):
    """
    Formata um valor numérico como moeda no padrão brasileiro
    
    Args:
        value: valor numérico
        
    Returns:
        str: valor formatado (ex: R$ 1.234,56)
    """
    return f"R$ {value:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.')