import pandas as pd
import numpy as np
from utils.stock_price import get_exchange_rate

def calculate_portfolio_metrics(portfolio_df):
    """
    Calcula as métricas do portfólio, suportando ativos em diferentes moedas.
    
    Args:
        portfolio_df: DataFrame com o portfólio incluindo preços atuais e informações de moeda
        
    Returns:
        dict: Dicionário com as métricas calculadas
    """
    # Verificar se o DataFrame está vazio
    if portfolio_df.empty:
        return {
            'total_investment': 0,
            'current_value': 0,
            'total_return': 0,
            'percent_return': 0,
            'best_performer': {'ticker': 'N/A', 'return_percent': 0},
            'worst_performer': {'ticker': 'N/A', 'return_percent': 0}
        }
    
    # Garantir que as colunas necessárias existem
    required_columns = ['ticker', 'preco_medio', 'quantidade']
    if not all(col in portfolio_df.columns for col in required_columns):
        missing = [col for col in required_columns if col not in portfolio_df.columns]
        raise ValueError(f"Colunas obrigatórias ausentes: {', '.join(missing)}")
    
    # Garantir que existe a coluna de preço atual
    if 'preco_atual' not in portfolio_df.columns:
        # Simular preços atuais (em uma aplicação real, estes viriam de uma API)
        np.random.seed(42)  # Para resultados consistentes
        portfolio_df['preco_atual'] = portfolio_df['preco_medio'] * (1 + np.random.uniform(-0.15, 0.25, len(portfolio_df)))
    
    # Cópia do DataFrame para trabalhar
    df = portfolio_df.copy()
    
    # Verificar se temos coluna de moeda, caso contrário assumir BRL para todos
    if 'moeda' not in df.columns:
        df['moeda'] = 'BRL'
    
    # Obter taxa de câmbio USD-BRL
    usd_brl_rate = get_exchange_rate('USD', 'BRL')
    
    # Calcular valores para cada ativo individualmente na moeda original
    df['valor_investido_orig'] = df['preco_medio'] * df['quantidade']
    df['valor_atual_orig'] = df['preco_atual'] * df['quantidade']
    
    # Converter para BRL para soma
    df['valor_investido_brl'] = df.apply(
        lambda row: row['valor_investido_orig'] * usd_brl_rate if row['moeda'] == 'USD' else row['valor_investido_orig'],
        axis=1
    )
    
    df['valor_atual_brl'] = df.apply(
        lambda row: row['valor_atual_orig'] * usd_brl_rate if row['moeda'] == 'USD' else row['valor_atual_orig'],
        axis=1
    )
    
    # Calcular retorno para cada ativo (na moeda original)
    df['retorno_valor_orig'] = df['valor_atual_orig'] - df['valor_investido_orig']
    df['retorno_percentual'] = (df['retorno_valor_orig'] / df['valor_investido_orig']) * 100
    
    # Calcular retorno em BRL para totais
    df['retorno_valor_brl'] = df['valor_atual_brl'] - df['valor_investido_brl']
    
    # Debug prints
    print(f"Total de ativos: {len(df)}")
    print(f"Total investido (BRL): {df['valor_investido_brl'].sum()}")
    print(f"Valor atual total (BRL): {df['valor_atual_brl'].sum()}")
    print(f"Retorno total (BRL): {df['retorno_valor_brl'].sum()}")
    if len(df[df['moeda'] == 'USD']) > 0:
        print(f"Ativos em USD: {len(df[df['moeda'] == 'USD'])}")
        print(f"Investimento em USD (original): {df[df['moeda'] == 'USD']['valor_investido_orig'].sum()}")
        print(f"Valor atual em USD (original): {df[df['moeda'] == 'USD']['valor_atual_orig'].sum()}")
        print(f"Investimento em USD (convertido para BRL): {df[df['moeda'] == 'USD']['valor_investido_brl'].sum()}")
        print(f"Valor atual em USD (convertido para BRL): {df[df['moeda'] == 'USD']['valor_atual_brl'].sum()}")
    
    # Calcular métricas do portfólio em BRL (totais)
    total_investment = df['valor_investido_brl'].sum()
    current_value = df['valor_atual_brl'].sum()
    total_return = df['retorno_valor_brl'].sum()
    percent_return = (total_return / total_investment) * 100 if total_investment > 0 else 0
    
    # Identificar melhor e pior ativo
    if len(df) > 0:
        best_idx = df['retorno_percentual'].idxmax()
        worst_idx = df['retorno_percentual'].idxmin()
        
        best_performer = {
            'ticker': df.loc[best_idx, 'ticker'],
            'return_percent': df.loc[best_idx, 'retorno_percentual']
        }
        
        worst_performer = {
            'ticker': df.loc[worst_idx, 'ticker'],
            'return_percent': df.loc[worst_idx, 'retorno_percentual']
        }
    else:
        best_performer = {'ticker': 'N/A', 'return_percent': 0}
        worst_performer = {'ticker': 'N/A', 'return_percent': 0}
    
    # Métricas por moeda
    currency_metrics = {}
    if len(df) > 0:
        currency_df = df.groupby('moeda').agg({
            'valor_investido_brl': 'sum',
            'valor_atual_brl': 'sum'
        }).reset_index()
        
        for _, row in currency_df.iterrows():
            currency = row['moeda']
            currency_metrics[currency] = {
                'investment': row['valor_investido_brl'],
                'current_value': row['valor_atual_brl'],
                'percentage': (row['valor_atual_brl'] / current_value) * 100 if current_value > 0 else 0
            }
    
    # Métricas por setor (se existir a coluna 'setor')
    sector_metrics = {}
    if 'setor' in df.columns:
        sector_df = df.groupby('setor').agg({
            'valor_investido_brl': 'sum',
            'valor_atual_brl': 'sum'
        }).reset_index()
        
        sector_df['retorno_valor'] = sector_df['valor_atual_brl'] - sector_df['valor_investido_brl']
        sector_df['retorno_percentual'] = (sector_df['retorno_valor'] / sector_df['valor_investido_brl']) * 100
        
        for _, row in sector_df.iterrows():
            sector_metrics[row['setor']] = {
                'investment': row['valor_investido_brl'],
                'current_value': row['valor_atual_brl'],
                'return': row['retorno_valor'],
                'percent_return': row['retorno_percentual']
            }
    
    # Para debug, inclua as colunas calculadas no portfólio
    portfolio_data = df
    
    return {
        'total_investment': total_investment,
        'current_value': current_value,
        'total_return': total_return,
        'percent_return': percent_return,
        'best_performer': best_performer,
        'worst_performer': worst_performer,
        'currency_metrics': currency_metrics,
        'sector_metrics': sector_metrics if 'setor' in df.columns else {},
        'portfolio_data': portfolio_data,
        'exchange_rate_usd_brl': usd_brl_rate
    }