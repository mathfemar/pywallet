import os
import pandas as pd
import numpy as np
from pathlib import Path
import streamlit as st
import re

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

def load_portfolio_with_currency(username):
    """
    Carrega o portfólio de um usuário, incluindo informações de moeda.
    
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
            
            # Adicionar coluna de moeda se não existir
            if 'moeda' not in df.columns:
                # Importar a função para verificar ações americanas
                from utils.stock_price import is_us_stock
                
                df['moeda'] = 'BRL'  # Valor padrão
                
                # Para cada ticker, identificar se é americano e ajustar a moeda
                for idx, row in df.iterrows():
                    ticker = row['ticker']
                    if is_us_stock(ticker):
                        df.at[idx, 'moeda'] = 'USD'
            
            return df
        
        except Exception as e:
            st.error(f"Erro ao carregar o portfólio: {str(e)}")
            return pd.DataFrame(columns=['ticker', 'preco_medio', 'quantidade', 'moeda'])
    else:
        return pd.DataFrame(columns=['ticker', 'preco_medio', 'quantidade', 'moeda'])

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
        
        # Salvar apenas as colunas necessárias (incluindo moeda se existir)
        columns_to_save = ['ticker', 'preco_medio', 'quantidade']
        if 'moeda' in df.columns:
            columns_to_save.append('moeda')
            
        df[columns_to_save].to_csv(file_path, index=False)
        
        return True
    
    except Exception as e:
        st.error(f"Erro ao salvar o portfólio: {str(e)}")
        return False

def save_portfolio_with_currency(username, portfolio_df):
    """
    Salva o portfólio de um usuário, incluindo informações de moeda.
    
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
        required_columns = ['ticker', 'preco_medio', 'quantidade', 'moeda']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        # Se a coluna de moeda estiver faltando, adicionar com valor padrão BRL
        if 'moeda' in missing_columns:
            df['moeda'] = 'BRL'
            missing_columns.remove('moeda')
            
        if missing_columns:
            raise ValueError(f"Colunas obrigatórias ausentes: {', '.join(missing_columns)}")
        
        # Normalizar tickers
        df['ticker'] = normalize_ticker(df['ticker'])
        
        # Salvar as colunas necessárias
        columns_to_save = ['ticker', 'preco_medio', 'quantidade', 'moeda']
        df[columns_to_save].to_csv(file_path, index=False)
        
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
            # Tentar ler o arquivo Excel com diferentes configurações
            # Primeiro, tentar ler normalmente com pandas
            try:
                df = pd.read_excel(file_obj)
                
                # Verificar se a primeira linha poderia ser cabeçalho
                first_row_is_header = True
                if len(df.columns) >= 3:
                    # Se as colunas não têm nomes significativos (0, 1, 2), a primeira linha pode não ser cabeçalho
                    if all(str(col).isdigit() for col in df.columns):
                        first_row_is_header = False
                    # Ou se os nomes das colunas são muito diferentes do esperado
                    column_names = [str(col).lower() for col in df.columns]
                    expected_names = ['ticker', 'preco', 'quantidade', 'ativo', 'preço', 'qtd', 'qtde', 'código', 'moeda']
                    if not any(expected in ' '.join(column_names) for expected in expected_names):
                        first_row_is_header = False
                
                # Se a primeira linha não parece ser cabeçalho, ler novamente sem cabeçalho
                if not first_row_is_header:
                    df = pd.read_excel(file_obj, header=None)
                    df.columns = ['ticker', 'preco_medio', 'quantidade']
                
            except Exception as e:
                # Se falhar, tentar ler sem cabeçalho
                file_obj.seek(0)
                df = pd.read_excel(file_obj, header=None)
                df.columns = ['ticker', 'preco_medio', 'quantidade']
                
        else:  # csv
            # Tentar diferentes delimitadores
            for sep in [';', ',', '\t']:
                try:
                    # Tentar com cabeçalho primeiro
                    df = pd.read_csv(file_obj, sep=sep)
                    
                    # Verificar se tem pelo menos 3 colunas
                    if len(df.columns) >= 3:
                        # Verificar se a primeira linha poderia ser cabeçalho
                        first_row_is_header = True
                        # Se as colunas não têm nomes significativos (0, 1, 2), a primeira linha pode não ser cabeçalho
                        if all(str(col).isdigit() for col in df.columns):
                            first_row_is_header = False
                        # Ou se os nomes das colunas são muito diferentes do esperado
                        column_names = [str(col).lower() for col in df.columns]
                        expected_names = ['ticker', 'preco', 'quantidade', 'ativo', 'preço', 'qtd', 'qtde', 'código', 'moeda']
                        if not any(expected in ' '.join(column_names) for expected in expected_names):
                            first_row_is_header = False
                        
                        # Se a primeira linha não parece ser cabeçalho, ler novamente sem cabeçalho
                        if not first_row_is_header:
                            file_obj.seek(0)
                            df = pd.read_csv(file_obj, sep=sep, header=None)
                            df.columns = ['ticker', 'preco_medio', 'quantidade']
                            
                        break
                    
                except:
                    # Reinicia o ponteiro do arquivo para tentar outro delimitador
                    file_obj.seek(0)
            else:
                # Se nenhum delimitador funcionou
                st.error("Não foi possível detectar o formato do arquivo CSV")
                return None
        
        # Se a importação tiver apenas 3 colunas sem cabeçalho, assume as colunas padrão
        if len(df.columns) == 3 and all(str(col).isdigit() for col in df.columns):
            df.columns = ['ticker', 'preco_medio', 'quantidade']
        elif len(df.columns) == 3:
            # Se tem 3 colunas mas com nomes personalizados, renomear para o padrão
            df.columns = ['ticker', 'preco_medio', 'quantidade']
        elif len(df.columns) == 4:
            # Se tem 4 colunas, assumir que a última é a moeda
            df.columns = ['ticker', 'preco_medio', 'quantidade', 'moeda']
        
        # Se tiver mais ou menos colunas, tentar identificar pelo conteúdo
        else:
            # Identificar coluna de ticker
            ticker_col = None
            price_col = None
            qty_col = None
            currency_col = None
            
            # Identificar coluna de ticker (procura por padrões como PETR4, VALE3)
            for col in df.columns:
                sample_values = df[col].dropna().astype(str).str.upper().tolist()[:10]
                # Se encontrar padrões de ticker em pelo menos 50% das amostras
                if sample_values and sum(1 for v in sample_values if re.match(r'^[A-Z]{3,6}[0-9]{1,2}$', v.strip()) or re.match(r'^[A-Z]{1,5}$', v.strip())) >= len(sample_values)/2:
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
                    # Verificar se a coluna contém valores que parecem ser quantidades (inteiros)
                    numeric_values = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')
                    if not numeric_values.isna().all() and (numeric_values % 1 == 0).all(skipna=True):
                        qty_col = col
                        break
                except:
                    continue
            
            # Identificar coluna de moeda (procura por "BRL", "USD", etc.)
            for col in df.columns:
                if col in [ticker_col, price_col, qty_col]:
                    continue
                
                sample_values = df[col].dropna().astype(str).str.upper().tolist()[:10]
                # Verificar se contém códigos de moeda
                if sample_values and sum(1 for v in sample_values if v.strip() in ['BRL', 'USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD', 'CHF']) >= len(sample_values)/2:
                    currency_col = col
                    break
            
            # Se identificou todas as colunas obrigatórias, renomear
            if ticker_col and price_col and qty_col:
                column_mapping = {
                    ticker_col: 'ticker',
                    price_col: 'preco_medio', 
                    qty_col: 'quantidade'
                }
                
                if currency_col:
                    column_mapping[currency_col] = 'moeda'
                
                df = df.rename(columns=column_mapping)
                
                # Selecionar apenas as colunas necessárias
                columns_to_keep = ['ticker', 'preco_medio', 'quantidade']
                if currency_col:
                    columns_to_keep.append('moeda')
                
                df = df[columns_to_keep]
            else:
                # Se não conseguiu identificar automaticamente, pegar as três primeiras colunas
                if len(df.columns) >= 3:
                    new_columns = list(df.columns)
                    column_mapping = {
                        new_columns[0]: 'ticker',
                        new_columns[1]: 'preco_medio',
                        new_columns[2]: 'quantidade'
                    }
                    
                    # Se tiver 4 colunas, assumir a quarta como moeda
                    if len(new_columns) >= 4:
                        column_mapping[new_columns[3]] = 'moeda'
                    
                    df = df.rename(columns=column_mapping)
                    
                    # Selecionar apenas as colunas necessárias
                    columns_to_keep = ['ticker', 'preco_medio', 'quantidade']
                    if len(new_columns) >= 4:
                        columns_to_keep.append('moeda')
                    
                    df = df[columns_to_keep]
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
        
        # 4. Moeda: padronizar
        if 'moeda' in df.columns:
            df['moeda'] = df['moeda'].str.upper().str.strip()
            # Padronizar valores comuns
            moeda_map = {
                'REAL': 'BRL',
                'REAIS': 'BRL',
                'R$': 'BRL',
                'DOLAR': 'USD',
                'DÓLAR': 'USD',
                'US$': 'USD',
                '$': 'USD',
                'EURO': 'EUR',
                '€': 'EUR'
            }
            df['moeda'] = df['moeda'].map(lambda x: moeda_map.get(x, x))
        
        return df
    
    except Exception as e:
        st.error(f"Erro ao processar arquivo: {str(e)}")
        return None

def process_imported_file_with_currency(file_obj, file_type=None):
    """
    Processa um arquivo importado com suporte a diferentes moedas.
    
    Args:
        file_obj: Objeto de arquivo (da função st.file_uploader)
        file_type: Tipo do arquivo ('xlsx' ou 'csv'), se None será determinado pela extensão
        
    Returns:
        DataFrame: Dados processados
    """
    # Primeiro, processar normalmente usando a função existente
    df = process_imported_file(file_obj, file_type)
    
    if df is None:
        return None
    
    # Importar a função para verificar ações americanas
    from utils.stock_price import is_us_stock
    
    # Adicionar coluna de moeda se não existir
    if 'moeda' not in df.columns:
        df['moeda'] = 'BRL'  # Valor padrão
        
        # Para cada ticker, identificar se é americano e ajustar a moeda
        for idx, row in df.iterrows():
            ticker = row['ticker']
            if is_us_stock(ticker):
                df.at[idx, 'moeda'] = 'USD'
    
    return df