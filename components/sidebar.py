import streamlit as st
import datetime

def create_sidebar(username="Usuário", is_debug=False):
    """
    Cria a barra lateral da aplicação.
    
    Args:
        username: Nome do usuário
        is_debug: Flag indicando se é modo de debug
    """
    with st.sidebar:
        # Cabeçalho
        st.title("PyWallet 💰")
        
        # Informações do usuário
        st.write(f"### Olá, {username}!")
        if is_debug:
            st.info("🛠️ Modo Debug Ativado")
            st.caption("Dados não serão salvos entre sessões")
        
        # Navegação
        st.subheader("Navegação")
        
        # Como estamos na página principal, vamos destacar a opção "Dashboard"
        st.markdown("**📊 Dashboard**")
        st.markdown("📝 Transações")
        st.markdown("📈 Desempenho")
        st.markdown("📋 Relatórios")
        
        # Filtros
        st.subheader("Filtros")
        
        # Data atual
        today = datetime.date.today()
        # Data exatamente um ano atrás
        one_year_ago = today.replace(year=today.year - 1)
        
        # Período de análise - data inicial é exatamente um ano atrás
        st.date_input(
            "Data Inicial",
            value=one_year_ago,
            key="date_from"
        )
        
        st.date_input(
            "Data Final",
            value=today,
            key="date_to"
        )
        
        # Opções de visualização
        st.checkbox("Mostrar valores em %", value=True, key="show_percentage")
        st.checkbox("Incluir dividendos", value=True, key="include_dividends")
        
        # Atualizar dados
        if st.button("🔄 Atualizar Dados"):
            st.success("Dados atualizados com sucesso!")
        
        # Rodapé
        st.markdown("---")
        
        # Se não estiver em modo debug, mostrar opção para importar novo portfólio
        if not is_debug:
            if st.button("📤 Importar Novo Portfólio"):
                st.session_state.portfolio_imported = False
                st.rerun()  # Alterado de experimental_rerun()
        
        # Botão de logout
        if st.button("🚪 Sair"):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.is_debug = False
            if 'portfolio_imported' in st.session_state:
                del st.session_state.portfolio_imported
            if 'debug_portfolio' in st.session_state:
                del st.session_state.debug_portfolio
            st.rerun()  # Alterado de experimental_rerun()
        
        # Informações da versão
        st.caption("PyWallet v1.0.0")
        st.caption(f"© {datetime.date.today().year} - Todos os direitos reservados")