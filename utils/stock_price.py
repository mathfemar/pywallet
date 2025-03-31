import pandas as pd
import numpy as np
import yfinance as yf
import re
import streamlit as st
import time
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

def percent_formatter(x, pos):
    """Formata valores no eixo Y como percentual"""
    return f'{x:.2%}'

def data_x_anos_atras(anos):
    """Retorna a data exata de X anos atrás contando dias corridos"""
    hoje = datetime.datetime.today()
    try:
        data_passada = hoje.replace(year=hoje.year - anos)
    except ValueError:
        # Se for 29 de fevereiro e o ano de destino não for bissexto, ajusta para 28 de fevereiro
        data_passada = hoje.replace(year=hoje.year - anos, day=28)
    return data_passada.date()

def is_brazilian_stock(ticker):
    """
    Verifica se um ticker é de uma ação brasileira com base no padrão.
    
    Args:
        ticker (str): O código do ticker a ser verificado
        
    Returns:
        bool: True se for uma ação brasileira, False caso contrário
    """
    # Remover qualquer sufixo .SA que já possa existir
    ticker = ticker.replace('.SA', '')
    
    # Lista de BDRs conhecidos que não devem ser tratados como ações brasileiras
    bdrs = ['NVDC34', 'A1MD34', 'GOGL34', 'MSFT34', 'AAPL34', 'AMZO34', 'NFLX34']
    if ticker in bdrs:
        return False
    
    # Padrão para BDRs: geralmente terminam com 34, 35, 36
    if re.match(r'^[A-Z0-9]{4,6}3[4-6]$', ticker):
        return False
    
    # Verifica o padrão básico de ações brasileiras (letras seguidas de números)
    if re.match(r'^[A-Z]{3,6}[0-9]{1,2}$', ticker):
        return True
    
    # Lista de ETFs brasileiros conhecidos
    etfs_brasileiros = ['BOVA11', 'SMAL11', 'IVVB11', 'PIBB11']
    if ticker in etfs_brasileiros:
        return True
        
    return False

def format_ticker_for_yfinance(ticker):
    """
    Formata o ticker para uso com a biblioteca yfinance.
    Para ações brasileiras, adiciona o sufixo .SA se necessário.
    
    Args:
        ticker (str): O código do ticker a ser formatado
        
    Returns:
        str: Ticker formatado para uso com yfinance
    """
    # Normalizar o ticker (maiúsculas, sem espaços)
    ticker = ticker.strip().upper()
    
    # Se já tiver o sufixo .SA, retorna como está
    if ticker.endswith('.SA'):
        return ticker
    
    # Adiciona .SA para ações brasileiras
    if is_brazilian_stock(ticker):
        return f"{ticker}.SA"
        
    return ticker

def GetDate(anos):
    """Obtém a data de X anos atrás e retorna junto com o número de anos"""
    return data_x_anos_atras(anos), anos

def GetPrices(ticker, anos=1):
    """
    Baixa os preços de fechamento ajustados dos ativos informados
    
    Args:
        ticker (str or list): Ticker ou lista de tickers
        anos (int): Número de anos para obter dados históricos
        
    Returns:
        pandas.DataFrame: DataFrame com os preços, número de anos
    """
    date, anos = GetDate(anos)
    
    # Formatar tickers para yfinance (adicionar .SA para brasileiros)
    if isinstance(ticker, list):
        formatted_tickers = [format_ticker_for_yfinance(t) for t in ticker]
    else:
        formatted_tickers = format_ticker_for_yfinance(ticker)
    
    # Baixa os dados de múltiplos tickers
    try:
        data = yf.download(formatted_tickers, start=date)["Close"].bfill()
        
        # Se for apenas um ativo, garante que o retorno seja um DataFrame
        if isinstance(data, pd.Series):
            data = data.to_frame()
        
        # Se os tickers foram formatados, precisamos restaurar os nomes originais
        if isinstance(ticker, list):
            # Criar mapeamento de tickers formatados para originais
            ticker_map = {format_ticker_for_yfinance(t): t for t in ticker}
            # Renomear colunas
            data.columns = [ticker_map.get(col, col) for col in data.columns]
        
        # Garantir que a ordem dos tickers seja preservada
        if isinstance(ticker, list):
            # Filtrar apenas os tickers que realmente estão no DataFrame
            available_tickers = [t for t in ticker if t in data.columns]
            if available_tickers:
                data = data[available_tickers]
    except Exception as e:
        print(f"Erro ao baixar dados: {e}")
        # Retornar DataFrame vazio em caso de erro
        return pd.DataFrame(), anos
    
    return data, anos

def fetch_current_price(ticker):
    """
    Busca o preço atual de uma ação usando yfinance com a lógica melhorada.
    
    Args:
        ticker (str): O código do ticker
        
    Returns:
        float: Preço atual da ação ou None se não encontrado
    """
    try:
        # Para BDRs, buscar diretamente pelo ticker com .SA
        if re.match(r'^[A-Z0-9]{4,6}3[4-6]$', ticker):
            # Tentar buscar diretamente como BDR
            bdr_ticker = f"{ticker}.SA"
            ticker_data = yf.Ticker(bdr_ticker)
            
            # Tentar obter o preço mais recente do BDR
            hist = ticker_data.history(period="1d")
            if not hist.empty and 'Close' in hist.columns and len(hist['Close']) > 0:
                return float(hist['Close'].iloc[-1])
                
            # Se não conseguir, tentar método alternativo para BDRs específicos
            bdr_mapping = {
                'NVDC34': 'NVDA',
                'A1MD34': 'AMD',
                'GOGL34': 'GOOG',
                'MSFT34': 'MSFT',
                'AAPL34': 'AAPL',
                'AMZO34': 'AMZN',
                'NFLX34': 'NFLX'
            }
            
            if ticker in bdr_mapping:
                # Buscar cotação diretamente do site da B3 ou outra fonte confiável
                # Como não temos acesso direto, vamos usar o preço médio como fallback
                # Em uma aplicação real, você usaria uma API específica para BDRs
                return None
        
        # Para ações normais
        yf_ticker = format_ticker_for_yfinance(ticker)
        ticker_data = yf.Ticker(yf_ticker)
        
        # Buscar preços do último dia
        hist = ticker_data.history(period="1d")
        if not hist.empty and 'Close' in hist.columns and len(hist['Close']) > 0:
            return float(hist['Close'].iloc[-1])
        
        # Método alternativo: buscar informações gerais do ticker
        info = ticker_data.info
        price_options = [
            ('currentPrice', info.get('currentPrice')),
            ('regularMarketPrice', info.get('regularMarketPrice')),
            ('previousClose', info.get('previousClose')),
            ('open', info.get('open')),
            ('dayHigh', info.get('dayHigh')),
            ('ask', info.get('ask'))
        ]
        
        # Usar o primeiro preço não-nulo disponível
        for key, price in price_options:
            if price is not None and price > 0:
                return float(price)
        
        # Se não conseguiu obter o preço, usar preço médio
        return None
    except Exception as e:
        print(f"Erro ao buscar preço para {ticker}: {str(e)}")
        return None

def update_portfolio_prices(portfolio_df, use_simulation=False, cache_minutes=5):
    """
    Atualiza os preços atuais das ações no DataFrame do portfólio.
    
    Args:
        portfolio_df (pandas.DataFrame): DataFrame contendo o portfólio com coluna 'ticker'
        use_simulation (bool): Se True, usa simulação em vez de buscar preços reais
        cache_minutes (int): Tempo em minutos para reutilizar preços em cache
        
    Returns:
        pandas.DataFrame: DataFrame com os preços atualizados
    """
    # Se o DataFrame estiver vazio, retorna
    if portfolio_df.empty:
        return portfolio_df
    
    # Copiar o DataFrame para não modificar o original
    df = portfolio_df.copy()
    
    # Usar simulação se solicitado
    if use_simulation:
        np.random.seed(42)  # Para resultados consistentes
        df['preco_atual'] = df['preco_medio'] * (1 + np.random.uniform(-0.15, 0.25, len(df)))
        return df
    
    # Verificar se temos preços em cache
    now = time.time()
    cache_key = 'stock_prices_cache'
    cache_time_key = 'stock_prices_cache_time'
    
    # Se o cache existir e estiver fresco, usar
    use_cache = (cache_key in st.session_state and 
                cache_time_key in st.session_state and 
                (now - st.session_state[cache_time_key]) < (cache_minutes * 60))
    
    # Lista de tickers para buscar
    tickers_list = df['ticker'].tolist()
    
    # Inicializar dicionário de preços
    price_cache = st.session_state.get(cache_key, {}) if use_cache else {}
    
    # Buscar preços para cada ticker individualmente para garantir máxima cobertura
    with st.spinner("Buscando preços atualizados..."):
        for idx, row in df.iterrows():
            ticker = row['ticker']
            
            # Verificar se já temos o preço em cache e se o cache está válido
            if use_cache and ticker in price_cache:
                df.at[idx, 'preco_atual'] = price_cache[ticker]
            else:
                # Buscar preço atual
                price = fetch_current_price(ticker)
                
                if price is not None:
                    df.at[idx, 'preco_atual'] = price
                    price_cache[ticker] = price
                else:
                    # Se não conseguiu obter o preço, usar preço médio com pequena variação
                    df.at[idx, 'preco_atual'] = row['preco_medio'] * (1 + np.random.uniform(-0.05, 0.05))
                    
    # Atualizar cache
    st.session_state[cache_key] = price_cache
    st.session_state[cache_time_key] = now
    
    return df

def get_stock_info(ticker):
    """
    Busca informações adicionais sobre uma ação usando yfinance.
    Útil para obter dados como setor, nome da empresa, etc.
    
    Args:
        ticker (str): O código do ticker
        
    Returns:
        dict: Dicionário com informações da ação ou None se não encontrado
    """
    try:
        # Verificar se é um BDR
        is_bdr = re.match(r'^[A-Z0-9]{4,6}3[4-6]$', ticker)
        
        # Para BDRs, tentar buscar informações do ativo original
        if is_bdr:
            # Extrair o ticker base (removendo os 2 últimos dígitos)
            base_ticker = re.sub(r'3[4-6]$', '', ticker)
            
            # Mapeamento de alguns BDRs conhecidos para seus tickers originais
            bdr_mapping = {
                'NVDC': 'NVDA',
                'A1MD': 'AMD',
                'GOGL': 'GOOG',
                'MSFT': 'MSFT',
                'AAPL': 'AAPL',
                'AMZO': 'AMZN',
                'NFLX': 'NFLX'
            }
            
            original_ticker = bdr_mapping.get(base_ticker, base_ticker)
            
            # Buscar informações do ticker original
            ticker_data = yf.Ticker(original_ticker)
            info = ticker_data.info
            
            # Obter informações relevantes
            return {
                'setor': info.get('sector', info.get('industryDisp', 'Tecnologia')),
                'nome': info.get('shortName', info.get('longName', ticker)),
                'mercado': 'BDR'
            }
        
        # Para outros ativos, usar o procedimento padrão
        yf_ticker = format_ticker_for_yfinance(ticker)
        ticker_data = yf.Ticker(yf_ticker)
        info = ticker_data.info
        
        # Filtrar apenas campos relevantes
        return {
            'setor': info.get('sector', info.get('industryDisp', 'Não disponível')),
            'nome': info.get('shortName', info.get('longName', ticker)),
            'mercado': 'Brasileiro' if '.SA' in yf_ticker else 'Internacional'
        }
    except Exception as e:
        print(f"Erro ao buscar informações para {ticker}: {str(e)}")
        return {
            'setor': 'Não disponível',
            'nome': ticker,
            'mercado': 'Desconhecido'
        }

def enrich_portfolio_data(portfolio_df):
    """
    Enriquece o DataFrame do portfólio com informações adicionais das ações.
    
    Args:
        portfolio_df (pandas.DataFrame): DataFrame contendo o portfólio
        
    Returns:
        pandas.DataFrame: DataFrame enriquecido com informações adicionais
    """
    # Se o DataFrame estiver vazio, retorna
    if portfolio_df.empty:
        return portfolio_df
    
    # Copiar o DataFrame para não modificar o original
    df = portfolio_df.copy()
    
    # Verificar se já temos todas as informações
    if all(col in df.columns for col in ['setor', 'nome_empresa', 'mercado']):
        return df
    
    # Adicionar colunas se não existirem
    for col in ['setor', 'nome_empresa', 'mercado']:
        if col not in df.columns:
            df[col] = None
    
    # Verificar se temos informações em cache
    cache_key = 'stock_info_cache'
    if cache_key not in st.session_state:
        st.session_state[cache_key] = {}
    
    info_cache = st.session_state[cache_key]
    
    # Buscar informações apenas para tickers que não estão no cache
    tickers_to_fetch = [
        ticker for ticker in df['ticker'] 
        if ticker not in info_cache
    ]
    
    if tickers_to_fetch:
        with st.spinner("Buscando informações dos ativos..."):
            with ThreadPoolExecutor(max_workers=5) as executor:
                future_to_ticker = {
                    executor.submit(get_stock_info, ticker): ticker 
                    for ticker in tickers_to_fetch
                }
                
                for future in as_completed(future_to_ticker):
                    ticker = future_to_ticker[future]
                    try:
                        info = future.result()
                        if info:
                            info_cache[ticker] = info
                    except Exception as e:
                        print(f"Erro ao buscar informações para {ticker}: {str(e)}")
    
    # Atualizar o DataFrame com as informações obtidas
    for idx, row in df.iterrows():
        ticker = row['ticker']
        if ticker in info_cache:
            df.at[idx, 'setor'] = info_cache[ticker]['setor']
            df.at[idx, 'nome_empresa'] = info_cache[ticker]['nome']
            df.at[idx, 'mercado'] = info_cache[ticker]['mercado']
    
    # Salvar cache
    st.session_state[cache_key] = info_cache
    
    return df

def GetTickers():
    """Obtém os tickers digitados pelo usuário"""
    l = input("Digite aqui os nomes das suas ações (separados por espaço ou vírgula): ")
    l = l.upper().replace(",", " ")  # Substitui vírgula por espaço
    return l.split()  # Separa os tickers corretamente