import streamlit as st
import datetime
import time
import pandas as pd
import numpy as np
import os
import sqlite3
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go

from utils.auth import check_password, create_user_if_not_exists
from utils.data_loader import (
    load_portfolio_with_currency, 
    save_portfolio_with_currency, 
    process_imported_file_with_currency, 
    format_currency_br
)

from utils.portfolio import calculate_portfolio_metrics
from utils.benchmark_comparison import calculate_benchmark_comparison, display_benchmark_kpi

from utils.auth import check_password, create_user_if_not_exists
from utils.data_loader import load_portfolio, save_portfolio, process_imported_file, format_currency_br
from utils.portfolio import calculate_portfolio_metrics
from utils.benchmark_comparison import calculate_benchmark_comparison, display_benchmark_kpi

import components.sidebar as sidebar_module
import components.charts as charts_module
import components.tables as tables_module
from utils.stock_price import update_portfolio_prices, enrich_portfolio_data

# Configuração da página
st.set_page_config(
    page_title="PyWallet - Gerenciador de Portfólio",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicialização de sessão
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'is_debug' not in st.session_state:
    st.session_state.is_debug = False

# Função de login
def login():
    st.title("PyWallet 💰")
    st.subheader("Gerenciador de Portfólio de Investimentos")
    
    with st.form("login_form"):
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            login_button = st.form_submit_button("Entrar")
        with col2:
            debug_mode = st.checkbox("Modo Debug", help="Modo para testes onde os dados não são salvos")
    
    if login_button:
        if debug_mode:
            st.session_state.authenticated = True
            st.session_state.username = "debug_user"
            st.session_state.is_debug = True
            st.success("Login realizado com sucesso no modo Debug!")
            st.rerun()  # Alterado de experimental_rerun()
        elif username and password:
            if check_password(username, password):
                st.session_state.authenticated = True
                st.session_state.username = username
                st.session_state.is_debug = False
                st.success("Login realizado com sucesso!")
                st.rerun()  # Alterado de experimental_rerun()
            else:
                # Criar novo usuário se não existir
                if create_user_if_not_exists(username, password):
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.is_debug = False
                    st.success("Novo usuário criado e login realizado com sucesso!")
                    st.rerun()  # Alterado de experimental_rerun()
                else:
                    st.error("Usuário ou senha incorretos!")
        else:
            st.warning("Por favor, preencha todos os campos.")

def import_portfolio():
    st.title("Importe seu Portfólio")
    
    import_method = st.radio(
        "Escolha como deseja importar seu portfólio",
        ["Upload de Arquivo", "Entrada Manual"]
    )
    
    if import_method == "Upload de Arquivo":
        st.subheader("Upload de Arquivo")
        
        file_format = st.radio(
            "Formato do arquivo",
            ["Excel (.xlsx)", "CSV (.csv)"]
        )
        
        uploaded_file = st.file_uploader(
            "Selecione seu arquivo", 
            type=["xlsx", "csv"] if file_format == "Excel (.xlsx)" else ["csv"]
        )
        
        # Mostrar tabela de exemplo diretamente na interface
        st.subheader("Exemplo de formato esperado")
        
        # Criar um DataFrame de exemplo (incluindo ativos americanos)
        exemplo_df = pd.DataFrame({
            'ticker': ['PETR4', 'VALE3', 'ITUB4', 'SPY', 'IEF'],
            'preco_medio': [22.50, 68.75, 32.10, 450.25, 92.30],
            'quantidade': [100, 50, 75, 5, 10],
            'moeda': ['BRL', 'BRL', 'BRL', 'USD', 'USD']  # Adicionamos a coluna de moeda
        })
        
        # Formatar preços para exibição - manter os preços originais na moeda correspondente
        exemplo_df_display = exemplo_df.copy()
        exemplo_df_display['preco_medio'] = exemplo_df_display.apply(
            lambda row: format_currency_br(row['preco_medio']) if row['moeda'] == 'BRL' 
            else f"US$ {row['preco_medio']:.2f}", axis=1
        )
        
        # Renomear colunas para exibição
        exemplo_df_display.columns = ['Código do Ativo', 'Preço Médio', 'Quantidade', 'Moeda']
        
        # Mostrar a tabela de exemplo
        st.table(exemplo_df_display)
        
        # Criar arquivo Excel para download com formatação correta
        import io
        import openpyxl
        
        # Criar um buffer de memória para o arquivo Excel
        buffer = io.BytesIO()
        
        # Criar um novo workbook Excel e selecionar a planilha ativa
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Portfolio"
        
        # Adicionar cabeçalhos
        ws.append(['ticker', 'preco_medio', 'quantidade', 'moeda'])
        
        # Adicionar dados de exemplo
        for _, row in exemplo_df.iterrows():
            ws.append([row['ticker'], row['preco_medio'], row['quantidade'], row['moeda']])
        
        # Salvar o workbook no buffer
        wb.save(buffer)
        buffer.seek(0)
        
        # Botão para download do modelo
        st.download_button(
            label="⬇️ Baixar modelo Excel",
            data=buffer,
            file_name="modelo_portfolio.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        if uploaded_file is not None:
            try:
                # Usar a função atualizada para processar o arquivo
                df = process_imported_file_with_currency(uploaded_file, 
                                          file_type='xlsx' if file_format == "Excel (.xlsx)" else 'csv')
                
                if df is not None:
                    # Mostrar prévia dos dados
                    st.subheader("Prévia dos Dados")
                    
                    # Criar uma cópia formatada para exibição - mantendo preços na moeda original
                    df_display = df.copy()
                    df_display['preco_medio'] = df_display.apply(
                        lambda row: format_currency_br(row['preco_medio']) if row['moeda'] == 'BRL' 
                        else f"US$ {row['preco_medio']:.2f}", axis=1
                    )
                    
                    st.dataframe(df_display)
                    
                    if st.button("Confirmar Importação"):
                        # Limpar cache para forçar atualização de preços
                        if 'stock_prices_cache' in st.session_state:
                            del st.session_state['stock_prices_cache']
                        if 'stock_prices_cache_time' in st.session_state:
                            del st.session_state['stock_prices_cache_time']
                            
                        if not st.session_state.is_debug:
                            save_portfolio_with_currency(st.session_state.username, df)
                            st.success("Portfólio importado com sucesso!")
                            st.session_state.portfolio_imported = True
                            st.rerun()
                        else:
                            st.session_state.debug_portfolio = df
                            st.success("Portfólio carregado em modo Debug!")
                            st.session_state.portfolio_imported = True
                            st.rerun()
                    
                    return df
                
            except Exception as e:
                st.error(f"Erro ao processar o arquivo: {str(e)}")
                return None
    
    else:  # Entrada Manual
        st.subheader("Entrada Manual")
        
        with st.form("manual_entry"):
            ticker = st.text_input("Código do Ativo (ex: PETR4 ou SPY)")
            
            # Adicionar seleção de moeda
            moeda = st.selectbox("Moeda", ["BRL", "USD"])
            
            # Ajustar o formato do campo de preço conforme a moeda selecionada
            preco_placeholder = "0,00" if moeda == "BRL" else "0.00"
            preco_help = "Use formato brasileiro (ex: 36,75)" if moeda == "BRL" else "Use formato americano (ex: 36.75)"
            preco_medio = st.text_input(
                "Preço Médio (R$)" if moeda == "BRL" else "Preço Médio (US$)", 
                value=preco_placeholder,
                help=preco_help
            )
            
            quantidade = st.number_input("Quantidade", min_value=1, step=1)
            
            submit_button = st.form_submit_button("Adicionar Ativo")
        
        if submit_button and ticker and preco_medio and quantidade:
            # Criar ou atualizar a lista temporária de ativos
            if 'temp_assets' not in st.session_state:
                st.session_state.temp_assets = []
            
            # Converter preço médio para float, respeitando formato brasileiro ou americano
            try:
                if moeda == "BRL":
                    preco_medio_float = float(preco_medio.replace('.', '').replace(',', '.'))
                else:  # USD - manter o preço em dólar
                    preco_medio_float = float(preco_medio)
            except:
                st.error(f"Formato de preço inválido. {preco_help}")
                return None
            
            # Adicionar o novo ativo
            st.session_state.temp_assets.append({
                'ticker': ticker.upper(),
                'preco_medio': preco_medio_float,
                'quantidade': quantidade,
                'moeda': moeda
            })
            
            st.success(f"Ativo {ticker.upper()} adicionado com sucesso!")
        
        # Mostrar ativos adicionados
        if 'temp_assets' in st.session_state and st.session_state.temp_assets:
            st.subheader("Ativos Adicionados")
            temp_df = pd.DataFrame(st.session_state.temp_assets)
            
            # Criar cópia formatada para exibição - mantendo preços na moeda original
            temp_df_display = temp_df.copy()
            temp_df_display['preco_medio'] = temp_df_display.apply(
                lambda row: format_currency_br(row['preco_medio']) if row['moeda'] == 'BRL' 
                else f"US$ {row['preco_medio']:.2f}", axis=1
            )
            
            st.dataframe(temp_df_display)
            
            if st.button("Confirmar Portfólio"):
                # Limpar cache para forçar atualização de preços
                if 'stock_prices_cache' in st.session_state:
                    del st.session_state['stock_prices_cache']
                if 'stock_prices_cache_time' in st.session_state:
                    del st.session_state['stock_prices_cache_time']
                    
                if not st.session_state.is_debug:
                    save_portfolio_with_currency(st.session_state.username, temp_df)
                    st.success("Portfólio salvo com sucesso!")
                    st.session_state.portfolio_imported = True
                    # Limpar ativos temporários
                    st.session_state.temp_assets = []
                    st.rerun()
                else:
                    st.session_state.debug_portfolio = temp_df
                    st.success("Portfólio carregado em modo Debug!")
                    st.session_state.portfolio_imported = True
                    # Limpar ativos temporários
                    st.session_state.temp_assets = []
                    st.rerun()
            
            return temp_df
    
    return None

def show_dashboard():
    # Carregar portfólio usando a nova função que suporta moedas diferentes
    if st.session_state.is_debug and 'debug_portfolio' in st.session_state:
        portfolio_df = st.session_state.debug_portfolio
    else:
        portfolio_df = load_portfolio_with_currency(st.session_state.username)
    
    # Verificar se o portfólio está vazio
    if portfolio_df.empty:
        st.info("Seu portfólio está vazio. Utilize a opção 'Importar Novo Portfólio' para começar.")
        return
    
    # Sidebar - Usamos a função diretamente do módulo
    sidebar_module.create_sidebar(st.session_state.username, st.session_state.is_debug)
    
    # Criar chave para controlar a atualização automática
    if 'dashboard_just_opened' not in st.session_state:
        st.session_state.dashboard_just_opened = True
        # Limpar cache para forçar atualização na primeira abertura
        if 'stock_prices_cache' in st.session_state:
            del st.session_state['stock_prices_cache']
        if 'stock_prices_cache_time' in st.session_state:
            del st.session_state['stock_prices_cache_time']
    
    # Botão para atualização manual dos preços
    col1, col2 = st.columns([3, 1])
    with col2:
        refresh_prices = st.button("🔄 Atualizar Preços", use_container_width=True)
        if refresh_prices:
            # Limpar cache para forçar nova consulta
            if 'stock_prices_cache' in st.session_state:
                del st.session_state['stock_prices_cache']
            if 'stock_prices_cache_time' in st.session_state:
                del st.session_state['stock_prices_cache_time']
    
    # Main content
    st.title("Dashboard - Visão Geral do Portfólio")
    
    # Mostrar mensagem de carregamento
    with st.spinner("Atualizando dados do mercado..."):
        # Atualizar preços das ações sempre - sem depender do modo debug
        # Usar a nova versão da função que suporta conversão de moeda
        portfolio_df = update_portfolio_prices(
            portfolio_df, 
            use_simulation=False,  # Nunca usar simulação, sempre buscar preços reais
            cache_minutes=5  # Cache de 5 minutos para não sobrecarregar a API
        )
        
        # Enriquecer dados com informações se não existirem
        if 'nome_empresa' not in portfolio_df.columns:
            portfolio_df = enrich_portfolio_data(portfolio_df)
    
    # Marcar que o dashboard não está mais sendo aberto pela primeira vez
    st.session_state.dashboard_just_opened = False
    
    # Calcular métricas do portfólio usando a função atualizada
    metrics = calculate_portfolio_metrics(portfolio_df)
    
    # Informação da última atualização
    now = datetime.datetime.now()
    st.caption(f"Última atualização: {now.strftime('%d/%m/%Y %H:%M:%S')}")
    
    # Se tivermos ativos em USD, mostrar a taxa de câmbio usada
    if metrics.get('exchange_rate_usd_brl'):
        st.caption(f"Taxa de câmbio USD/BRL: {metrics['exchange_rate_usd_brl']:.4f}")
    
    # KPI Cards com 5 colunas para incluir o pior ativo
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            label="Valor Total", 
            value=format_currency_br(metrics['current_value'])
        )
    
    with col2:
        st.metric(
            label="Investimento", 
            value=format_currency_br(metrics['total_investment'])
        )
    
    with col3:
        st.metric(
            label="Retorno (R$)", 
            value=format_currency_br(metrics['total_return']),
            delta=f"{metrics['percent_return']:.2f}%"
        )
    
    with col4:
        st.metric(
            label="Melhor Ativo", 
            value=f"{metrics['best_performer']['ticker']}",
            delta=f"{metrics['best_performer']['return_percent']:.2f}%"
        )
    
    with col5:
        st.metric(
            label="Pior Ativo", 
            value=f"{metrics['worst_performer']['ticker']}",
            delta=f"{metrics['worst_performer']['return_percent']:.2f}%"
        )
    
    # Removida a seção de distribuição por moeda conforme solicitado
    
    # Calcular comparação com benchmarks
    start_date = st.session_state.get('date_from', datetime.date.today() - datetime.timedelta(days=365))
    end_date = st.session_state.get('date_to', datetime.date.today())
    
    benchmark_comparison = calculate_benchmark_comparison(
        metrics['total_investment'],
        metrics['current_value'],
        start_date,
        end_date
    )

    # Separador
    st.markdown("---")
    
    # Gráficos
    st.subheader("Visualização do Portfólio")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Mostrar distribuição por ativo
        fig_distribution = charts_module.plot_portfolio_distribution(portfolio_df)
        st.plotly_chart(fig_distribution, use_container_width=True)
    
    with col2:
        fig_performance = charts_module.plot_historical_performance(metrics['total_investment'], metrics['current_value'])
        st.plotly_chart(fig_performance, use_container_width=True)

    # Exibir KPI de comparação com benchmarks
    display_benchmark_kpi(
        benchmark_comparison['portfolio_return'],
        benchmark_comparison['benchmarks']
    )
    
    # Separador
    st.markdown("---")
    
    # Tabela de ativos
    st.subheader("Seus Ativos")
    tables_module.display_assets_table(portfolio_df)
    
# Fluxo principal da aplicação
def main():
    # Verifique se o usuário está autenticado
    if not st.session_state.authenticated:
        login()
    else:
        # Verifique se o usuário tem um portfólio (ou está em modo debug)
        if st.session_state.is_debug:
            if 'portfolio_imported' not in st.session_state or not st.session_state.portfolio_imported:
                import_portfolio()
            else:
                show_dashboard()
        else:
            # Verifica se existe um portfólio para o usuário
            portfolio_exists = os.path.exists(f"data/portfolios/{st.session_state.username}.csv")
            
            if not portfolio_exists:
                import_portfolio()
            else:
                show_dashboard()

if __name__ == "__main__":
    # Garantir que as pastas necessárias existam
    os.makedirs("data/portfolios", exist_ok=True)
    
    main()