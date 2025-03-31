import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import datetime

def plot_portfolio_distribution(portfolio_df):
    """
    Cria um gráfico de pizza da distribuição do portfólio por ativo.
    
    Args:
        portfolio_df: DataFrame com o portfólio
        
    Returns:
        figura do Plotly
    """
    # Usar a distribuição por ativo (ticker)
    dist_df = portfolio_df.copy()
    
    # Calcular valor atual total para cada ativo
    if 'valor_atual' not in dist_df.columns:
        dist_df['valor_atual'] = dist_df['preco_atual'] * dist_df['quantidade']
    
    # Calcular percentual de cada ativo
    dist_df['percentual'] = (dist_df['valor_atual'] / dist_df['valor_atual'].sum()) * 100
    
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
        values='valor_atual',
        names='ticker',
        title='Distribuição por Ativo',
        labels={'valor_atual': 'Valor Atual', 'ticker': 'Ativo'},
        hover_data=['percentual'],
        custom_data=['percentual'],
        color_discrete_sequence=colors
    )
    
    # Formato do hover
    fig.update_traces(
        hovertemplate='<b>%{label}</b><br>Valor: R$ %{value:.2f}<br>Percentual: %{customdata[0]:.2f}%'
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
    Cria um gráfico de linha do desempenho histórico simulado.
    
    Args:
        initial_value: Valor inicial do investimento
        current_value: Valor atual do investimento
        n_months: Número de meses para simular
        
    Returns:
        figura do Plotly
    """
    # Gerar datas para os últimos n meses
    today = datetime.date.today()
    dates = [today - datetime.timedelta(days=30*i) for i in range(n_months, -1, -1)]
    dates = [d.strftime('%b/%Y') for d in dates]
    
    # Simular valores para o período
    np.random.seed(42)  # Para resultados consistentes
    
    # Cria uma progressão que começa no valor inicial e termina no valor atual
    growth_factor = (current_value / initial_value) ** (1 / n_months)
    
    values = [initial_value]
    for i in range(1, n_months):
        # Adiciona uma variação aleatória ao crescimento esperado
        random_factor = 1 + np.random.uniform(-0.03, 0.03)
        values.append(values[-1] * growth_factor * random_factor)
    
    # Garantir que o último valor é o current_value
    values.append(current_value)
    
    # Criar DataFrame
    df = pd.DataFrame({
        'data': dates,
        'valor': values
    })
    
    # Calcular percentual de crescimento
    initial = df['valor'].iloc[0]
    df['percentual'] = ((df['valor'] / initial) - 1) * 100
    
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
    
    # Configuração do layout
    fig.update_layout(
        title='Evolução do Portfólio',
        xaxis_title='Mês/Ano',
        yaxis_title='Valor (R$)',
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5
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