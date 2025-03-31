import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import datetime
import streamlit as st

def plot_portfolio_distribution(portfolio_df):
    """
    Cria um gráfico de pizza da distribuição do portfólio por ativo.
    Respeita a moeda original de cada ativo para calcular a distribuição.
    
    Args:
        portfolio_df: DataFrame com o portfólio
        
    Returns:
        figura do Plotly
    """
    # Usar a distribuição por ativo (ticker)
    dist_df = portfolio_df.copy()
    
    # Verificar se temos os valores apropriados para usar
    if 'valor_atual_orig' in dist_df.columns:
        # Usar valores na moeda original para cálculo de percentuais
        values_column = 'valor_atual_orig'
    elif 'valor_atual' in dist_df.columns:
        # Fallback para coluna tradicional
        values_column = 'valor_atual'
    else:
        # Calcular valor na hora se não existir
        dist_df['valor_atual_orig'] = dist_df['preco_atual'] * dist_df['quantidade']
        values_column = 'valor_atual_orig'
    
    # Para mostrar valores originais no hover, vamos criar colunas formatadas
    if 'moeda' in dist_df.columns:
        dist_df['valor_formatado'] = dist_df.apply(
            lambda row: f"R$ {row[values_column]:,.2f}" if row['moeda'] == 'BRL' 
            else f"US$ {row[values_column]:,.2f}", 
            axis=1
        )
    else:
        dist_df['valor_formatado'] = dist_df[values_column].apply(lambda x: f"R$ {x:,.2f}")
    
    # Para o cálculo das proporções, precisamos de todos os valores em uma moeda
    # Se temos moedas diferentes, vamos criar outro campo com todos convertidos para BRL
    if 'moeda' in dist_df.columns and 'USD' in dist_df['moeda'].values:
        # Buscar taxa de câmbio
        from utils.stock_price import get_exchange_rate
        usd_brl_rate = get_exchange_rate('USD', 'BRL')
        
        # Criar coluna com valores convertidos para usar no cálculo percentual
        dist_df['valor_brl'] = dist_df.apply(
            lambda row: row[values_column] * usd_brl_rate if row['moeda'] == 'USD' else row[values_column],
            axis=1
        )
        
        # Calcular percentual baseado nos valores em BRL
        total_value_brl = dist_df['valor_brl'].sum()
        dist_df['percentual'] = (dist_df['valor_brl'] / total_value_brl) * 100
    else:
        # Se tudo está na mesma moeda, é mais simples
        total_value = dist_df[values_column].sum()
        dist_df['percentual'] = (dist_df[values_column] / total_value) * 100
    
    # Ordenar por valor para garantir cores consistentes (maiores valores com cores mais escuras)
    dist_df = dist_df.sort_values('percentual', ascending=False)
    
    # Criar uma paleta de cores do azul marinho escuro ao branco
    # O número de cores deve corresponder ao número de ativos
    import plotly.colors as pc
    num_colors = len(dist_df)
    color_scale = pc.sequential.Blues[::-1]  # Inverte para começar do mais escuro
    
    # Criar um array de cores com gradação apropriada
    colors = pc.sample_colorscale(color_scale, [i/(num_colors-1) for i in range(num_colors)]) if num_colors > 1 else [color_scale[0]]
    
    # Criar gráfico
    fig = px.pie(
        dist_df,
        values='percentual',  # Usando o percentual calculado corretamente
        names='ticker',
        title='Distribuição por Ativo',
        hover_data=['valor_formatado', 'percentual'],  # Incluir valor formatado no hover
        custom_data=['valor_formatado', 'percentual'],
        color_discrete_sequence=colors
    )
    
    # Formato do hover customizado para mostrar moeda correta
    fig.update_traces(
        hovertemplate='<b>%{label}</b><br>Valor: %{customdata[0]}<br>Percentual: %{customdata[1]:.2f}%'
    )
    
    # Configuração do layout
    fig.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5
        )
    )
    
    return fig

def plot_historical_performance(initial_value, current_value, n_months=6):
    """
    Cria um gráfico de linha do desempenho histórico simulado, incluindo o CDI como comparação.
    
    Args:
        initial_value: Valor inicial do investimento
        current_value: Valor atual do investimento
        n_months: Número de meses para simular
        
    Returns:
        figura do Plotly
    """
    # Obter datas do sidebar se disponíveis, ou criar um período padrão
    start_date = st.session_state.get('date_from', 
                  datetime.date.today() - datetime.timedelta(days=365))
    end_date = st.session_state.get('date_to', datetime.date.today())
    
    # Calcular número de meses entre as datas
    delta = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
    n_months = max(delta, 1)  # No mínimo 1 mês
    
    # Gerar datas mensais entre data inicial e final
    dates = []
    current_date = datetime.date(start_date.year, start_date.month, 1)
    
    while current_date <= end_date:
        dates.append(current_date)
        # Avançar para o próximo mês
        if current_date.month == 12:
            current_date = datetime.date(current_date.year + 1, 1, 1)
        else:
            current_date = datetime.date(current_date.year, current_date.month + 1, 1)
    
    # Formatar datas para exibição
    date_labels = [d.strftime('%b/%Y') for d in dates]
    
    # Calcular trajetória de crescimento progressivo entre valor inicial e final
    if len(dates) <= 1:
        # Se tiver apenas uma data, criar array com valor inicial e atual
        values = [initial_value, current_value]
        date_labels = [start_date.strftime('%b/%Y'), end_date.strftime('%b/%Y')]
    else:
        # Cálculo do fator de crescimento mensal
        growth_factor = (current_value / initial_value) ** (1 / (len(dates) - 1)) if initial_value > 0 else 1
        
        # Gerar valores suavizados com componente aleatório controlado
        np.random.seed(42)  # Para resultados consistentes
        values = [initial_value]
        
        for i in range(1, len(dates)):
            # Componente aleatório menor para trajetória mais suave
            random_factor = 1 + np.random.uniform(-0.02, 0.02)
            next_value = values[-1] * growth_factor * random_factor
            values.append(next_value)
        
        # Ajustar o último valor para garantir que é exatamente o current_value
        values[-1] = current_value
    
    # Criar DataFrame
    df = pd.DataFrame({
        'data': date_labels,
        'valor': values
    })
    
    # Calcular percentual de crescimento
    df['percentual'] = ((df['valor'] / initial_value) - 1) * 100
    
    # Criar gráfico
    fig = go.Figure()
    
    # Adicionar linha principal
    fig.add_trace(
        go.Scatter(
            x=df['data'],
            y=df['valor'],
            mode='lines+markers',
            name='Valor do Portfólio',
            line=dict(color='#0088FE', width=3),
            hovertemplate='<b>%{x}</b><br>Valor: R$ %{y:.2f}<br>Retorno: %{customdata:.2f}%',
            customdata=df['percentual']
        )
    )
    
    # Adicionar linha de referência do valor inicial
    fig.add_trace(
        go.Scatter(
            x=[df['data'].iloc[0], df['data'].iloc[-1]],
            y=[initial_value, initial_value],
            mode='lines',
            name='Valor Inicial',
            line=dict(color='rgba(0, 0, 0, 0.3)', width=2, dash='dash'),
            hoverinfo='skip'
        )
    )
    
    # Adicionar linha do CDI
    # Simular rendimento do CDI (aproximadamente 0.9% ao mês no período)
    # Em uma aplicação real, você buscaria os valores reais do CDI
    cdi_monthly_rate = 0.009  # 0.9% ao mês, valor aproximado
    cdi_values = [initial_value]
    
    for i in range(1, len(dates)):
        cdi_values.append(cdi_values[0] * (1 + cdi_monthly_rate) ** i)
    
    fig.add_trace(
        go.Scatter(
            x=df['data'],
            y=cdi_values,
            mode='lines',
            name='CDI',
            line=dict(color='#FFBB00', width=2, dash='dot'),
            hovertemplate='<b>%{x}</b><br>Valor: R$ %{y:.2f}<br>Retorno: %{customdata:.2f}%',
            customdata=[(val/initial_value - 1) * 100 for val in cdi_values]
        )
    )
    
    # Configuração do layout com legenda melhorada
    fig.update_layout(
        title='Evolução do Portfólio',
        xaxis_title='Mês/Ano',
        yaxis_title='Valor (R$)',
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,  # Posicionar acima do gráfico
            xanchor="right",
            x=1,
            bgcolor="rgba(255, 255, 255, 0.1)",
            bordercolor="rgba(255, 255, 255, 0.2)",
            borderwidth=1
        )
    )
    
    # Formato do eixo Y
    fig.update_yaxes(tickprefix='R$ ')
    
    return fig

def plot_performance_comparison(portfolio_df):
    """
    Cria um gráfico de barras comparando o desempenho dos ativos.
    
    Args:
        portfolio_df: DataFrame com o portfólio
        
    Returns:
        figura do Plotly
    """
    # Ordenar por retorno percentual
    df = portfolio_df.sort_values('retorno_percentual', ascending=False)
    
    # Criar cores baseadas no retorno (positivo = verde, negativo = vermelho)
    colors = ['#4CAF50' if x >= 0 else '#F44336' for x in df['retorno_percentual']]
    
    # Criar gráfico
    fig = go.Figure()
    
    # Adicionar barras
    fig.add_trace(
        go.Bar(
            x=df['ticker'],
            y=df['retorno_percentual'],
            marker_color=colors,
            text=df['retorno_percentual'].apply(lambda x: f"{x:.2f}%"),
            textposition='auto',
            hovertemplate='<b>%{x}</b><br>Retorno: %{y:.2f}%<br>Valor Atual: R$ %{customdata[0]:.2f}<br>Investimento: R$ %{customdata[1]:.2f}',
            customdata=df[['valor_atual', 'valor_investido']]
        )
    )
    
    # Adicionar linha de referência em 0%
    fig.add_shape(
        type="line",
        x0=-0.5,
        y0=0,
        x1=len(df)-0.5,
        y1=0,
        line=dict(
            color="rgba(0, 0, 0, 0.5)",
            width=2,
            dash="dash",
        )
    )
    
    # Configuração do layout
    fig.update_layout(
        title='Desempenho por Ativo (%)',
        xaxis_title='Ativo',
        yaxis_title='Retorno (%)',
        yaxis=dict(
            ticksuffix='%'
        )
    )
    
    return fig