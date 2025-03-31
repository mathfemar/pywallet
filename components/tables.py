import streamlit as st
import pandas as pd
import numpy as np
from utils.data_loader import format_currency_br

def display_assets_table(portfolio_df):
    """
    Exibe uma tabela com os ativos do portfólio.
    
    Args:
        portfolio_df: DataFrame com o portfólio
    """
    if portfolio_df.empty:
        st.info("Nenhum ativo encontrado no portfólio.")
        return
    
    # Garantir que temos as colunas necessárias
    if not all(col in portfolio_df.columns for col in ['valor_investido', 'valor_atual', 'retorno_valor', 'retorno_percentual']):
        # Calcular valores se não existirem
        portfolio_df['valor_investido'] = portfolio_df['preco_medio'] * portfolio_df['quantidade']
        portfolio_df['valor_atual'] = portfolio_df['preco_atual'] * portfolio_df['quantidade']
        portfolio_df['retorno_valor'] = portfolio_df['valor_atual'] - portfolio_df['valor_investido']
        portfolio_df['retorno_percentual'] = (portfolio_df['retorno_valor'] / portfolio_df['valor_investido']) * 100
    
    # Criar cópia para exibição
    display_df = portfolio_df.copy()
    
    # Remover coluna de setor se existir
    if 'setor' in display_df.columns:
        display_df = display_df.drop(columns=['setor'])
    
    # Renomear colunas para exibição
    column_mapping = {
        'ticker': 'Ativo',
        'quantidade': 'Quantidade',
        'preco_medio': 'Preço Médio',
        'preco_atual': 'Preço Atual',
        'valor_investido': 'Valor Investido',
        'valor_atual': 'Valor Atual',
        'retorno_valor': 'Retorno (R$)',
        'retorno_percentual': 'Retorno (%)'
    }
    
    # Selecionar colunas disponíveis
    available_columns = [col for col in column_mapping.keys() if col in display_df.columns]
    display_df = display_df[available_columns].rename(columns={k: v for k, v in column_mapping.items() if k in available_columns})
    
    # Formatar valores numéricos em formato brasileiro
    for col in ['Preço Médio', 'Preço Atual', 'Valor Investido', 'Valor Atual', 'Retorno (R$)']:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(format_currency_br)
    
    # Formatar percentuais
    if 'Retorno (%)' in display_df.columns:
        display_df['Retorno (%)'] = display_df['Retorno (%)'].apply(lambda x: f"{x:.2f}%")
    
    # Criar lista de estilização para destacar valores positivos e negativos
    if 'Retorno (R$)' in display_df.columns:
        # Preparar dados originais para estilização
        numeric_return = portfolio_df['retorno_valor']
        
        # Mapear índices positivos e negativos
        positive_indices = numeric_return > 0
        negative_indices = numeric_return < 0
        
        # Aplicar estilo com base no valor original
        styled_df = display_df.style
        
        # Aplicar cores às células de retorno
        styled_df = styled_df.apply(lambda _: [
            'color: #4CAF50; font-weight: bold' if pos else 
            'color: #F44336; font-weight: bold' if neg else ''
            for pos, neg in zip(positive_indices, negative_indices)
        ], subset=['Retorno (R$)', 'Retorno (%)'])
        
        # Exibir tabela estilizada
        st.dataframe(
            styled_df,
            hide_index=True,
            use_container_width=True
        )
    else:
        # Exibir tabela normal
        st.dataframe(
            display_df,
            hide_index=True,
            use_container_width=True
        )

def display_sector_table(portfolio_df):
    """
    Exibe uma tabela com os setores do portfólio.
    
    Args:
        portfolio_df: DataFrame com o portfólio
    """
    if 'setor' not in portfolio_df.columns:
        st.info("Informações de setor não disponíveis.")
        return
    
    # Agrupar por setor
    sector_df = portfolio_df.groupby('setor').agg({
        'valor_investido': 'sum',
        'valor_atual': 'sum'
    }).reset_index()
    
    # Calcular métricas
    sector_df['retorno_valor'] = sector_df['valor_atual'] - sector_df['valor_investido']
    sector_df['retorno_percentual'] = (sector_df['retorno_valor'] / sector_df['valor_investido']) * 100
    sector_df['percentual_carteira'] = (sector_df['valor_atual'] / sector_df['valor_atual'].sum()) * 100
    
    # Renomear colunas para exibição
    display_df = sector_df.rename(columns={
        'setor': 'Setor',
        'valor_investido': 'Valor Investido',
        'valor_atual': 'Valor Atual',
        'retorno_valor': 'Retorno (R$)',
        'retorno_percentual': 'Retorno (%)',
        'percentual_carteira': 'Alocação (%)'
    })
    
    # Formatar valores em formato brasileiro
    display_df['Valor Investido'] = display_df['Valor Investido'].apply(format_currency_br)
    display_df['Valor Atual'] = display_df['Valor Atual'].apply(format_currency_br)
    display_df['Retorno (R$)'] = display_df['Retorno (R$)'].apply(format_currency_br)
    display_df['Retorno (%)'] = display_df['Retorno (%)'].apply(lambda x: f"{x:.2f}%")
    display_df['Alocação (%)'] = display_df['Alocação (%)'].apply(lambda x: f"{x:.2f}%")
    
    # Preparar dados originais para estilização
    numeric_return = sector_df['retorno_valor']
    
    # Mapear índices positivos e negativos
    positive_indices = numeric_return > 0
    negative_indices = numeric_return < 0
    
    # Aplicar estilo com base no valor original
    styled_df = display_df.style
    
    # Aplicar cores às células de retorno
    styled_df = styled_df.apply(lambda _: [
        'color: #4CAF50; font-weight: bold' if pos else 
        'color: #F44336; font-weight: bold' if neg else ''
        for pos, neg in zip(positive_indices, negative_indices)
    ], subset=['Retorno (R$)', 'Retorno (%)'])
    
    # Exibir tabela estilizada
    st.dataframe(
        styled_df,
        hide_index=True,
        use_container_width=True
    )