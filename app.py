import streamlit as st
import pandas as pd
import numpy as np
import os
import sqlite3
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go

# Importações diretas dos módulos
from utils.auth import check_password, create_user_if_not_exists
from utils.data_loader import load_portfolio, save_portfolio, process_imported_file, format_currency_br
from utils.portfolio import calculate_portfolio_metrics
import components.sidebar as sidebar_module
import components.charts as charts_module
import components.tables as tables_module

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

# Função para importação inicial de portfólio
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
        
        if uploaded_file is not None:
            try:
                # Usar a função simplificada para processar o arquivo
                df = process_imported_file(uploaded_file, 
                                          file_type='xlsx' if file_format == "Excel (.xlsx)" else 'csv')
                
                if df is not None:
                    # Mostrar prévia dos dados
                    st.subheader("Prévia dos Dados")
                    
                    # Criar uma cópia formatada para exibição
                    df_display = df.copy()
                    df_display['preco_medio'] = df_display['preco_medio'].apply(format_currency_br)
                    
                    st.dataframe(df_display)
                    
                    if st.button("Confirmar Importação"):
                        if not st.session_state.is_debug:
                            save_portfolio(st.session_state.username, df)
                            st.success("Portfólio importado com sucesso!")
                            st.session_state.portfolio_imported = True
                            st.rerun()  # Alterado de experimental_rerun()
                        else:
                            st.session_state.debug_portfolio = df
                            st.success("Portfólio carregado em modo Debug!")
                            st.session_state.portfolio_imported = True
                            st.rerun()  # Alterado de experimental_rerun()
                    
                    return df
                
            except Exception as e:
                st.error(f"Erro ao processar o arquivo: {str(e)}")
                return None
    
    else:  # Entrada Manual
        st.subheader("Entrada Manual")
        
        with st.form("manual_entry"):
            ticker = st.text_input("Código do Ativo (ex: PETR4)")
            preco_medio = st.text_input("Preço Médio (R$)", value="0,00")
            quantidade = st.number_input("Quantidade", min_value=1, step=1)
            
            submit_button = st.form_submit_button("Adicionar Ativo")
        
        if submit_button and ticker and preco_medio and quantidade:
            # Criar ou atualizar a lista temporária de ativos
            if 'temp_assets' not in st.session_state:
                st.session_state.temp_assets = []
            
            # Converter preço médio de formato brasileiro para float
            try:
                preco_medio_float = float(preco_medio.replace('.', '').replace(',', '.'))
            except:
                st.error("Formato de preço inválido. Use o formato brasileiro (ex: 36,75)")
                return None
            
            # Adicionar o novo ativo
            st.session_state.temp_assets.append({
                'ticker': ticker.upper(),
                'preco_medio': preco_medio_float,
                'quantidade': quantidade
            })
            
            st.success(f"Ativo {ticker.upper()} adicionado com sucesso!")
        
        # Mostrar ativos adicionados
        if 'temp_assets' in st.session_state and st.session_state.temp_assets:
            st.subheader("Ativos Adicionados")
            temp_df = pd.DataFrame(st.session_state.temp_assets)
            
            # Criar cópia formatada para exibição
            temp_df_display = temp_df.copy()
            temp_df_display['preco_medio'] = temp_df_display['preco_medio'].apply(format_currency_br)
            
            st.dataframe(temp_df_display)
            
            if st.button("Confirmar Portfólio"):
                if not st.session_state.is_debug:
                    save_portfolio(st.session_state.username, temp_df)
                    st.success("Portfólio salvo com sucesso!")
                    st.session_state.portfolio_imported = True
                    # Limpar ativos temporários
                    st.session_state.temp_assets = []
                    st.rerun()  # Alterado de experimental_rerun()
                else:
                    st.session_state.debug_portfolio = temp_df
                    st.success("Portfólio carregado em modo Debug!")
                    st.session_state.portfolio_imported = True
                    # Limpar ativos temporários
                    st.session_state.temp_assets = []
                    st.rerun()  # Alterado de experimental_rerun()
            
            return temp_df
    
    return None

# Função principal que exibe o dashboard
def show_dashboard():
    # Carregar portfólio
    if st.session_state.is_debug and 'debug_portfolio' in st.session_state:
        portfolio_df = st.session_state.debug_portfolio
    else:
        portfolio_df = load_portfolio(st.session_state.username)
    
    # Simulando preços atuais (em uma aplicação real, estes viriam de uma API)
    # Aqui estamos adicionando uma variação aleatória ao preço médio para simular
    np.random.seed(42)  # Para resultados consistentes
    portfolio_df['preco_atual'] = portfolio_df['preco_medio'] * (1 + np.random.uniform(-0.15, 0.25, len(portfolio_df)))
    
    # Simulando setores (em uma aplicação real, estes viriam de uma API ou banco de dados)
    sectors = ['Financeiro', 'Tecnologia', 'Energia', 'Consumo', 'Saúde', 'Industrial', 'Materiais']
    portfolio_df['setor'] = np.random.choice(sectors, len(portfolio_df))
    
    # Calcular métricas do portfólio
    metrics = calculate_portfolio_metrics(portfolio_df)
    
    # Sidebar - Usamos a função diretamente do módulo
    sidebar_module.create_sidebar(st.session_state.username, st.session_state.is_debug)
    
    # Main content
    st.title("Dashboard - Visão Geral do Portfólio")
    
    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    
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
    
    # Gráficos
    st.subheader("Visualização do Portfólio")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_distribution = charts_module.plot_portfolio_distribution(portfolio_df)
        st.plotly_chart(fig_distribution, use_container_width=True)
    
    with col2:
        fig_performance = charts_module.plot_historical_performance(metrics['total_investment'], metrics['current_value'])
        st.plotly_chart(fig_performance, use_container_width=True)
    
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