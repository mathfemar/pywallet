import streamlit as st
import pandas as pd
import numpy as np
import datetime
from utils.data_loader import format_currency_br

def calculate_benchmark_comparison(initial_value, current_value, start_date, end_date):
    """
    Calcula a comparação entre o retorno do portfólio e benchmarks de mercado.
    
    Args:
        initial_value: Valor inicial do investimento
        current_value: Valor atual do investimento
        start_date: Data inicial do período
        end_date: Data final do período
        
    Returns:
        dict: Dicionário com comparações de benchmarks
    """
    # Calcular retorno do portfólio
    portfolio_return = ((current_value / initial_value) - 1) * 100
    
    # Calcular retorno do CDI (simulado por enquanto)
    # Número de meses no período
    months_diff = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
    if months_diff < 1:
        months_diff = 1
        
    # Taxa CDI média mensal (usamos 0.9% ~= 11.5% a.a.)
    cdi_monthly = 0.009
    
    # Calcula retorno acumulado no período
    cdi_return = ((1 + cdi_monthly) ** months_diff - 1) * 100
    
    # Calcular % do CDI 
    cdi_percentage = (portfolio_return / cdi_return) * 100 if cdi_return > 0 else 0
    
    # Preparar outros benchmarks (placeholders para implementação futura)
    # IPCA, IBOV, etc. seriam calculados de forma semelhante com dados reais
    benchmarks = {
        'CDI': {
            'return': cdi_return,
            'portfolio_vs_benchmark': portfolio_return - cdi_return,
            'percentage_of_benchmark': cdi_percentage
        },
        'IPCA': {
            'return': 0,  # Placeholder para implementação futura
            'portfolio_vs_benchmark': 0,
            'percentage_of_benchmark': 0
        },
        'IPCA+6%': {
            'return': 0,  # Placeholder para implementação futura
            'portfolio_vs_benchmark': 0,
            'percentage_of_benchmark': 0  
        },
        'IBOV': {
            'return': 0,  # Placeholder para implementação futura
            'portfolio_vs_benchmark': 0,
            'percentage_of_benchmark': 0
        }
    }
    
    return {
        'portfolio_return': portfolio_return,
        'benchmarks': benchmarks
    }

def display_benchmark_kpi(portfolio_return, benchmarks):
    """
    Exibe o KPI de comparação com benchmarks.
    
    Args:
        portfolio_return: Retorno percentual do portfólio
        benchmarks: Dicionário com comparações de benchmarks
    """
    st.subheader("Comparação com Benchmarks")
    
    # Criar colunas para exibir os benchmarks
    cols = st.columns(4)
    
    # Exibir KPI do CDI (único implementado por enquanto)
    with cols[0]:
        cdi_data = benchmarks['CDI']
        
        # Criar o delta (diferença entre portfólio e CDI)
        delta_value = f"{cdi_data['portfolio_vs_benchmark']:.2f}%"
        
        # Determinar se a comparação é positiva ou negativa para formatação
        is_positive = cdi_data['portfolio_vs_benchmark'] > 0
        
        # Título do card
        st.markdown("### CDI")
        
        # Valor do benchmark
        st.markdown(f"**Retorno CDI:** {cdi_data['return']:.2f}%")
        
        # Comparação percentual (portfólio vs benchmark)
        if is_positive:
            st.markdown(f"**Diferença:** <span style='color:green'>+{delta_value}</span>", unsafe_allow_html=True)
        else:
            st.markdown(f"**Diferença:** <span style='color:red'>{delta_value}</span>", unsafe_allow_html=True)
            
        # Percentual do CDI alcançado
        st.markdown(f"**% do CDI:** {cdi_data['percentage_of_benchmark']:.2f}%")
    
    # Exibir placeholders para outros benchmarks futuros
    with cols[1]:
        st.markdown("### IPCA")
        st.markdown("*Implementação futura*")
    
    with cols[2]:
        st.markdown("### IPCA+6%")
        st.markdown("*Implementação futura*")
    
    with cols[3]:
        st.markdown("### IBOVESPA")
        st.markdown("*Implementação futura*")

# Função para obter dados reais do CDI (usando a API do Banco Central)
def get_cdi_data(start_date, end_date):
    """
    Tenta obter dados do CDI do Banco Central do Brasil.
    Se não estiver disponível, simula os dados.
    
    Args:
        start_date: Data inicial
        end_date: Data final
    
    Returns:
        DataFrame: Dados do CDI
    """
    try:
        # Verificar se a biblioteca sgs-data está disponível
        try:
            import sgs
            # Código 12 = CDI diário no SGS/BCB
            cdi_data = sgs.get({'cdi': 12}, start=start_date, end=end_date)
            
            if not cdi_data.empty:
                # Converter taxas diárias para acumulado
                cdi_data['cdi_acumulado'] = (1 + cdi_data['cdi']/100).cumprod() - 1
                return cdi_data
        except ImportError:
            pass
    except Exception as e:
        print(f"Erro ao obter dados do CDI: {str(e)}")
    
    # Fallback para simulação
    return simulate_cdi_data(start_date, end_date)

def simulate_cdi_data(start_date, end_date):
    """
    Simula dados do CDI para o período.
    
    Args:
        start_date: Data inicial
        end_date: Data final
    
    Returns:
        DataFrame: Dados simulados do CDI
    """
    # Criar uma série temporal diária
    date_range = pd.date_range(start=start_date, end=end_date, freq='B')
    
    # CDI diário médio (aproximadamente 0.045% ao dia = ~11.5% a.a.)
    daily_cdi = 0.00045
    
    # Criar DataFrame
    df = pd.DataFrame(index=date_range)
    df['cdi'] = daily_cdi * 100  # Em percentual
    
    # Calcular acumulado
    df['cdi_acumulado'] = (1 + daily_cdi).cumprod() - 1
    
    return df