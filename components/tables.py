import streamlit as st
import pandas as pd
import numpy as np
from utils.data_loader import format_currency_br

def display_assets_table(portfolio_df):
    """
    Exibe uma tabela com os ativos do portfólio, otimizada para mostrar todos
    os ativos sem necessidade de scroll e respeitando a moeda original.
    
    Args:
        portfolio_df: DataFrame com o portfólio
    """
    if portfolio_df.empty:
        st.info("Nenhum ativo encontrado no portfólio.")
        return
    
    # Garantir que temos as colunas necessárias para exibição
    # Criar cópia para exibição
    display_df = portfolio_df.copy()
    
    # Verificar se temos as colunas de valor calculadas
    recalculate_values = False
    required_columns = ['valor_investido_orig', 'valor_atual_orig', 'retorno_valor_orig', 'retorno_percentual']
    
    if not all(col in display_df.columns for col in required_columns):
        recalculate_values = True
    
    # Se precisamos recalcular os valores
    if recalculate_values:
        # Verificar se temos dados de moeda
        if 'moeda' not in display_df.columns:
            display_df['moeda'] = 'BRL'
            
        # Se tivermos ativos em USD, precisamos da taxa de câmbio
        from utils.stock_price import get_exchange_rate
        usd_brl_rate = get_exchange_rate('USD', 'BRL')
        
        # Calcular valores na moeda original
        display_df['valor_investido_orig'] = display_df['preco_medio'] * display_df['quantidade']
        display_df['valor_atual_orig'] = display_df['preco_atual'] * display_df['quantidade']
        display_df['retorno_valor_orig'] = display_df['valor_atual_orig'] - display_df['valor_investido_orig']
        display_df['retorno_percentual'] = (display_df['retorno_valor_orig'] / display_df['valor_investido_orig']) * 100
        
        # Valores em BRL para totais
        display_df['valor_investido_brl'] = display_df.apply(
            lambda row: row['valor_investido_orig'] * usd_brl_rate if row['moeda'] == 'USD' else row['valor_investido_orig'],
            axis=1
        )
        
        display_df['valor_atual_brl'] = display_df.apply(
            lambda row: row['valor_atual_orig'] * usd_brl_rate if row['moeda'] == 'USD' else row['valor_atual_orig'],
            axis=1
        )
        
        display_df['retorno_valor_brl'] = display_df['valor_atual_brl'] - display_df['valor_investido_brl']
    
    # Remover coluna de setor se existir para economizar espaço
    if 'setor' in display_df.columns:
        display_df = display_df.drop(columns=['setor'])
    
    # Preparar colunas para exibição
    display_columns = ['ticker', 'quantidade']
    
    # Mostrar preços na moeda original
    if 'moeda' in display_df.columns:
        display_df['preco_medio_display'] = display_df.apply(
            lambda row: format_currency_br(row['preco_medio']) if row['moeda'] == 'BRL' 
            else f"US$ {row['preco_medio']:.2f}", axis=1
        )
        
        display_df['preco_atual_display'] = display_df.apply(
            lambda row: format_currency_br(row['preco_atual']) if row['moeda'] == 'BRL' 
            else f"US$ {row['preco_atual']:.2f}", axis=1
        )
        
        # Adicionar colunas formatadas para exibição
        display_columns.extend(['preco_medio_display', 'preco_atual_display'])
    else:
        # Caso não tenha coluna de moeda, usar formatação padrão
        display_df['preco_medio_display'] = display_df['preco_medio'].apply(format_currency_br)
        display_df['preco_atual_display'] = display_df['preco_atual'].apply(format_currency_br)
        display_columns.extend(['preco_medio_display', 'preco_atual_display'])
    
    # Valores de investimento e valor atual
    display_df['valor_investido_display'] = display_df.apply(
        lambda row: format_currency_br(row['valor_investido_orig']) if row['moeda'] == 'BRL'
        else f"US$ {row['valor_investido_orig']:.2f}", axis=1
    )
    
    display_df['valor_atual_display'] = display_df.apply(
        lambda row: format_currency_br(row['valor_atual_orig']) if row['moeda'] == 'BRL'
        else f"US$ {row['valor_atual_orig']:.2f}", axis=1
    )
    
    display_columns.extend(['valor_investido_display', 'valor_atual_display'])
    
    # Retornos (na moeda original)
    display_df['retorno_valor_display'] = display_df.apply(
        lambda row: format_currency_br(row['retorno_valor_orig']) if row['moeda'] == 'BRL'
        else f"US$ {row['retorno_valor_orig']:.2f}", axis=1
    )
    
    display_df['retorno_percentual_display'] = display_df['retorno_percentual'].apply(lambda x: f"{x:.2f}%")
    display_columns.extend(['retorno_valor_display', 'retorno_percentual_display'])
    
    # Renomear colunas para exibição
    column_mapping = {
        'ticker': 'Ativo',
        'quantidade': 'Quantidade',
        'preco_medio_display': 'Preço Médio',
        'preco_atual_display': 'Preço Atual',
        'valor_investido_display': 'Valor Investido',
        'valor_atual_display': 'Valor Atual',
        'retorno_valor_display': 'Retorno',
        'retorno_percentual_display': 'Retorno (%)'
    }
    
    # Criar DataFrame final para exibição
    final_df = display_df[display_columns].rename(columns=column_mapping)
    
    # Preparar dados para estilização
    positive_indices = display_df['retorno_percentual'] > 0
    negative_indices = display_df['retorno_percentual'] < 0
    
    # Aplicar estilo com base no valor original
    styled_df = final_df.style
    
    # Aplicar cores às células de retorno
    styled_df = styled_df.apply(lambda _: [
        'color: #4CAF50; font-weight: bold' if pos else 
        'color: #F44336; font-weight: bold' if neg else ''
        for pos, neg in zip(positive_indices, negative_indices)
    ], subset=['Retorno', 'Retorno (%)'])
    
    # Determinar a altura adequada da tabela com base no número de ativos
    num_assets = len(display_df)
    
    # Altura por linha (ajuste de acordo com o número de ativos)
    if num_assets <= 5:
        height_per_row = 50  # Mais espaço para poucos ativos
    elif num_assets <= 10:
        height_per_row = 40  # Tamanho médio
    else:
        height_per_row = 35  # Compacto para muitos ativos
    
    # Altura total = linhas * altura por linha + cabeçalho (35px) + margem (10px)
    table_height = (num_assets * height_per_row) + 35 + 10
    
    # Exibir tabela estilizada com altura customizada
    st.dataframe(
        styled_df,
        hide_index=True,
        use_container_width=True,
        height=table_height  # Altura personalizada para evitar scroll
    )