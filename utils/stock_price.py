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

def get_exchange_rate(from_currency='USD', to_currency='BRL'):
    """
    Obtém a taxa de câmbio atual entre duas moedas.
    
    Args:
        from_currency: Moeda de origem (padrão: USD)
        to_currency: Moeda de destino (padrão: BRL)
        
    Returns:
        float: Taxa de câmbio atual
    """
    try:
        # Verificar se temos a taxa em cache e se está fresca (menos de 1 hora)
        cache_key = f'exchange_rate_{from_currency}_{to_currency}'
        cache_time_key = f'exchange_rate_time_{from_currency}_{to_currency}'
        
        now = time.time()
        cache_valid = (
            cache_key in st.session_state and 
            cache_time_key in st.session_state and
            (now - st.session_state[cache_time_key]) < 3600  # 1 hora em segundos
        )
        
        if cache_valid:
            return st.session_state[cache_key]
        
        # Não temos cache válido, buscar taxa atual
        # Usar o símbolo para o par de moedas no Yahoo Finance
        symbol = f"{from_currency}{to_currency}=X"
        currency_data = yf.Ticker(symbol)
        
        # Obter o preço mais recente
        latest_data = currency_data.history(period="1d")
        
        if not latest_data.empty:
            rate = latest_data['Close'].iloc[-1]
            
            # Salvar em cache
            st.session_state[cache_key] = rate
            st.session_state[cache_time_key] = now
            
            return rate
        else:
            # Fallback: se não conseguir obter, usar uma taxa aproximada
            # Você pode ajustar este valor ou implementar outra fonte de dados
            fallback_rate = 5.0 if from_currency == 'USD' and to_currency == 'BRL' else 1.0
            st.warning(f"Não foi possível obter taxa de câmbio atualizada. Usando taxa aproximada: {fallback_rate}")
            return fallback_rate
            
    except Exception as e:
        print(f"Erro ao obter taxa de câmbio: {str(e)}")
        # Fallback para caso de erro
        fallback_rate = 5.0 if from_currency == 'USD' and to_currency == 'BRL' else 1.0
        st.warning(f"Erro ao obter taxa de câmbio. Usando taxa aproximada: {fallback_rate}")
        return fallback_rate

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

def is_us_stock(ticker):
    """
    Verifica se um ticker é de uma ação/ETF americana.
    
    Args:
        ticker (str): O código do ticker a ser verificado
        
    Returns:
        bool: True se for uma ação americana, False caso contrário
    """
    # Lista de padrões comuns para ações americanas
    # Tickers de ETFs comuns dos EUA
    us_etfs = [
        'SPY', 'VOO', 'QQQ', 'IVV', 'VTI', 'SPYI', 'IEF', 'TLT', 
        'AGG', 'BND', 'VEA', 'VWO', 'GLD', 'VIG', 'VXUS', 'SPHD'
    ]
    
    # Remover qualquer sufixo existente
    clean_ticker = ticker.upper().replace('.US', '')
    
    # Verificar se está na lista de ETFs conhecidos
    if clean_ticker in us_etfs:
        return True
    
    # Verificar o padrão de ticker americano (letras sem números no final)
    if re.match(r'^[A-Z]{1,5}$', clean_ticker):
        # Evitar falsos positivos com ações brasileiras de 3-4 letras (ex: VALE, PETR)
        brazilian_stocks = ['VALE', 'PETR', 'ITUB', 'BBDC', 'BBAS', 'ABEV', 'ITSA']
        if clean_ticker not in brazilian_stocks:
            return True
    
    return False

def format_ticker_for_yfinance(ticker):
    """
    Formata o ticker para uso com a biblioteca yfinance.
    Suporta ações brasileiras (.SA) e americanas.
    
    Args:
        ticker (str): O código do ticker a ser formatado
        
    Returns:
        str: Ticker formatado para uso com yfinance
    """
    # Normalizar o ticker (maiúsculas, sem espaços)
    ticker = ticker.strip().upper()
    
    # Se já tiver sufixo, retorna como está
    if ticker.endswith('.SA') or ticker.endswith('.US'):
        return ticker.replace('.US', '')  # Remove .US pois não é necessário no yfinance
    
    # Verificar se é ação brasileira ou americana
    if is_brazilian_stock(ticker):
        return f"{ticker}.SA"
    elif is_us_stock(ticker):
        return ticker  # Tickers americanos não precisam de sufixo no yfinance
        
    # Se não conseguir determinar, assume que é brasileiro (padrão mais seguro)
    return f"{ticker}.SA"

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
    Busca o preço atual de uma ação usando yfinance com suporte a ações americanas.
    
    Args:
        ticker (str): O código do ticker
        
    Returns:
        tuple: (preço atual, moeda)
    """
    try:
        # Determinar se é ação americana ou brasileira
        is_us = is_us_stock(ticker)
        
        # Formatar ticker para yfinance
        yf_ticker = format_ticker_for_yfinance(ticker)
        ticker_data = yf.Ticker(yf_ticker)
        
        # Buscar preços do último dia
        hist = ticker_data.history(period="1d")
        
        if not hist.empty and 'Close' in hist.columns and len(hist['Close']) > 0:
            price = float(hist['Close'].iloc[-1])
            currency = 'USD' if is_us else 'BRL'
            return price, currency
        
        # Método alternativo: buscar informações gerais do ticker
        info = ticker_data.info
        
        # Campo currentPrice nem sempre está disponível, tentar alternativas
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
                # Determinar a moeda com base no tipo de ação
                currency = 'USD' if is_us else 'BRL'
                return float(price), currency
        
        # Se não conseguiu obter o preço, retornar None
        return None, None
        
    except Exception as e:
        print(f"Erro ao buscar preço para {ticker}: {str(e)}")
        return None, None

def update_portfolio_prices(portfolio_df, use_simulation=False, cache_minutes=5):
    """
    Atualiza os preços atuais das ações no DataFrame do portfólio,
    incluindo conversão de preços em USD para BRL.
    
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
    
    # Garantir que existe a coluna de moeda
    if 'moeda' not in df.columns:
        df['moeda'] = 'BRL'  # Assumir BRL como padrão
    
    # Usar simulação se solicitado
    if use_simulation:
        np.random.seed(42)  # Para resultados consistentes
        df['preco_atual'] = df.apply(
            lambda row: row['preco_medio'] * (1 + np.random.uniform(-0.15, 0.25)),
            axis=1
        )
        return df
    
    # Verificar se temos preços em cache
    now = time.time()
    cache_key = 'stock_prices_cache'
    cache_time_key = 'stock_prices_cache_time'
    
    # Se o cache existir e estiver fresco, usar
    use_cache = (cache_key in st.session_state and 
                cache_time_key in st.session_state and 
                (now - st.session_state[cache_time_key]) < (cache_minutes * 60))
    
    # Inicializar dicionário de preços
    price_cache = st.session_state.get(cache_key, {}) if use_cache else {}
    
    # Buscar taxa de câmbio USD-BRL
    usd_brl_rate = get_exchange_rate('USD', 'BRL')
    
    # Buscar preços para cada ticker individualmente
    with st.spinner("Buscando preços atualizados..."):
        for idx, row in df.iterrows():
            ticker = row['ticker']
            
            # Verificar se já temos o preço em cache e se o cache está válido
            if use_cache and ticker in price_cache:
                price_info = price_cache[ticker]
                
                # Atualizar com valores do cache
                if row['moeda'] == 'USD':
                    # Se o preço médio está em USD, o preço atual também será em USD para comparação
                    df.at[idx, 'preco_atual'] = price_info['original_price']
                    df.at[idx, 'preco_atual_brl'] = price_info['price_brl']  # Versão em BRL para cálculos
                else:
                    df.at[idx, 'preco_atual'] = price_info['price_brl']
                
                df.at[idx, 'preco_original'] = price_info['original_price']
                df.at[idx, 'moeda_original'] = price_info['currency']
            else:
                # Buscar preço atual
                price, currency = fetch_current_price(ticker)
                
                if price is not None:
                    if row['moeda'] == 'USD':
                        # Se o preço médio está em USD, manter o preço atual também em USD
                        df.at[idx, 'preco_atual'] = price
                        df.at[idx, 'preco_atual_brl'] = price * usd_brl_rate  # Versão em BRL para cálculos
                    else:
                        # Para ativos em BRL, usar o preço em BRL diretamente
                        if currency == 'USD':
                            # Converter para BRL se necessário
                            df.at[idx, 'preco_atual'] = price * usd_brl_rate
                        else:
                            df.at[idx, 'preco_atual'] = price
                    
                    df.at[idx, 'preco_original'] = price
                    df.at[idx, 'moeda_original'] = currency
                    
                    # Atualizar cache
                    price_cache[ticker] = {
                        'price_brl': price * usd_brl_rate if currency == 'USD' else price,
                        'original_price': price,
                        'currency': currency
                    }
                else:
                    # Se não conseguiu obter o preço, usar preço médio com pequena variação
                    random_factor = 1 + np.random.uniform(-0.05, 0.05)
                    df.at[idx, 'preco_atual'] = row['preco_medio'] * random_factor
                    
                    if row['moeda'] == 'USD':
                        df.at[idx, 'preco_atual_brl'] = row['preco_medio'] * random_factor * usd_brl_rate
                    
                    df.at[idx, 'preco_original'] = df.at[idx, 'preco_atual']
                    df.at[idx, 'moeda_original'] = row['moeda']
    
    # Atualizar cache
    st.session_state[cache_key] = price_cache
    st.session_state[cache_time_key] = now
    
    return df

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
        is_us = is_us_stock(ticker)
        
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
        
        # Para ações americanas
        elif is_us:
            yf_ticker = ticker  # Ticker americano sem modificação
            ticker_data = yf.Ticker(yf_ticker)
            info = ticker_data.info
            
            return {
                'setor': info.get('sector', info.get('industryDisp', 'Não disponível')),
                'nome': info.get('shortName', info.get('longName', ticker)),
                'mercado': 'EUA'
            }
        
        # Para ações brasileiras ou outros ativos
        else:
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

def GetTickers():
    """Obtém os tickers digitados pelo usuário"""
    l = input("Digite aqui os nomes das suas ações (separados por espaço ou vírgula): ")
    l = l.upper().replace(",", " ")  # Substitui vírgula por espaço
    return l.split()  # Separa os tickers corretamente