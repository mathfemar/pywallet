import pandas as pd
import numpy as np

def calculate_portfolio_metrics(portfolio_df):
    """
    Calcula as métricas do portfólio.
    
    Args:
        portfolio_df: DataFrame com o portfólio incluindo preços atuais
        
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
    
    # Calcular valores totais por ativo
    portfolio_df['valor_investido'] = portfolio_df['preco_medio'] * portfolio_df['quantidade']
    portfolio_df['valor_atual'] = portfolio_df['preco_atual'] * portfolio_df['quantidade']
    portfolio_df['retorno_valor'] = portfolio_df['valor_atual'] - portfolio_df['valor_investido']
    portfolio_df['retorno_percentual'] = (portfolio_df['retorno_valor'] / portfolio_df['valor_investido']) * 100
    
    # Calcular métricas do portfólio
    total_investment = portfolio_df['valor_investido'].sum()
    current_value = portfolio_df['valor_atual'].sum()
    total_return = current_value - total_investment
    percent_return = (total_return / total_investment) * 100 if total_investment > 0 else 0
    
    # Identificar melhor e pior ativo
    best_idx = portfolio_df['retorno_percentual'].idxmax()
    worst_idx = portfolio_df['retorno_percentual'].idxmin()
    
    best_performer = {
        'ticker': portfolio_df.loc[best_idx, 'ticker'],
        'return_percent': portfolio_df.loc[best_idx, 'retorno_percentual']
    }
    
    worst_performer = {
        'ticker': portfolio_df.loc[worst_idx, 'ticker'],
        'return_percent': portfolio_df.loc[worst_idx, 'retorno_percentual']
    }
    
    # Métricas por setor (se existir a coluna 'setor')
    sector_metrics = {}
    if 'setor' in portfolio_df.columns:
        sector_df = portfolio_df.groupby('setor').agg({
            'valor_investido': 'sum',
            'valor_atual': 'sum'
        }).reset_index()
        
        sector_df['retorno_valor'] = sector_df['valor_atual'] - sector_df['valor_investido']
        sector_df['retorno_percentual'] = (sector_df['retorno_valor'] / sector_df['valor_investido']) * 100
        
        for _, row in sector_df.iterrows():
            sector_metrics[row['setor']] = {
                'investment': row['valor_investido'],
                'current_value': row['valor_atual'],
                'return': row['retorno_valor'],
                'percent_return': row['retorno_percentual']
            }
    
    return {
        'total_investment': total_investment,
        'current_value': current_value,
        'total_return': total_return,
        'percent_return': percent_return,
        'best_performer': best_performer,
        'worst_performer': worst_performer,
        'sector_metrics': sector_metrics if 'setor' in portfolio_df.columns else {},
        'portfolio_data': portfolio_df
    }