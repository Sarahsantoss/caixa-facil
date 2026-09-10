import streamlit as st
import pandas as pd
import calendar
from datetime import date
from supabase import create_client, Client

# =========================================================
# 1. CONFIGURAÇÃO DA PÁGINA E ESTILO OTIMIZADO PARA CELULAR
# =========================================================
st.set_page_config(page_title="Caixa Fácil", layout="centered", initial_sidebar_state="collapsed")

# Estilo CSS para transformar o site em um App de Banco nativo no celular
st.markdown("""
    <style>
    /* Esconde cabeçalhos, rodapé padrão e menu do Streamlit */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Fontes maiores e fácil leitura na tela do celular */
    html, body, [class*="css"], .stMarkdown, p, label {
        font-size: 18px !important;
    }

    /* Espaçamento no fundo para o conteúdo não ser coberto pela barra inferior */
    .main .block-container {
        padding-top: 15px !important;
        padding-bottom: 120px !important;
        padding-left: 15px !important;
        padding-right: 15px !important;
    }

    /* Botões grandes e fáceis de tocar com o polegar */
    div.stButton > button {
        width: 100% !important;
        height: 3.4em !important;
        font-size: 18px !important;
        font-weight: bold !important;
        border-radius: 12px !important;
    }

    /* BARRA FIXA NO RODAPÉ DA TELA DO CELULAR (ESTILO BANCO) */
    div[data-testid="stBottomBlockContainer"] {
        position: fixed !important;
        bottom: 0 !important;
        left: 0 !important;
        right: 0 !important;
        background-color: #ffffff !important;
        border-top: 2px solid #e2e8f0 !important;
        padding: 8px 6px 22px 6px !important; /* Espaço inferior para gestos do iPhone/Android */
        z-index: 999999 !important;
        box-shadow: 0px -4px 12px rgba(0, 0, 0, 0.08);
    }

    /* Botões da barra inferior */
    div[data-testid="stBottomBlockContainer"] div[role="radiogroup"] {
        display: flex !important;
        justify-content: space-around !important;
        gap: 4px !important;
    }
    
    div[data-testid="stBottomBlockContainer"] label {
        flex: 1 !important;
        background-color: #f1f5f9 !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 10px !important;
        padding: 10px 2px !important;
        text-align: center !important;
        font-size: 13px !important;
        font-weight: bold !important;
        color: #334155 !important;
    }

    /* Botão ativado na barra inferior */
    div[data-testid="stBottomBlockContainer"] label[data-checked="true"] {
        background-color: #0284c7 !important;
        color: #ffffff !important;
        border-color: #0284c7 !important;
    }
    </style>
""", unsafe_allow_html=True)


# =========================================================
# 2. CONEXÃO COM O BANCO DE DADOS NA NUVEM (Supabase)
# =========================================================
# Substitua com as suas credenciais do Supabase
SUPABASE_URL = "https://pasmbmpgxuirnhlpwojf.supabase.co"
SUPABASE_KEY = "sb_publishable_XeiQp6uaRZ0Pby1B6QL_Kw_MMGu0AM2"

@st.cache_resource
def conectar_banco():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = conectar_banco()


# =========================================================
# 3. TELA DE SEGURANÇA E ACESSO
# =========================================================
SENHA_CAIXA = "1234"  # <-- Altere para a senha que preferir

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.title("🔒 Acesso ao Caixa")
    senha_digitada = st.text_input("Digite a Senha para Entrar:", type="password")
    
    if st.button("ENTRAR NO SISTEMA"):
        if senha_digitada == SENHA_CAIXA:
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("Senha incorreta! Tente novamente.")
    st.stop()

# Opção de bloqueio na barra lateral
if st.sidebar.button("🔒 Sair / Bloquear App"):
    st.session_state.autenticado = False
    st.rerun()

st.title("📱 Caixa Fácil")


# =========================================================
# 4. CONTROLE DAS TELAS (BARRA DE NAVEGAÇÃO INFERIOR)
# =========================================================
OPCOES_NAVEGACAO = [
    "➕ Novo", 
    "📋 Lista", 
    "📊 Fechamento", 
    "📅 Mensal"
]

if "tela_ativa" not in st.session_state:
    st.session_state.tela_ativa = "➕ Novo"

tela = st.session_state.tela_ativa


# =========================================================
# TELA 1: REALIZAR NOVO LANÇAMENTO
# =========================================================
if tela == "➕ Novo":
    st.subheader("➕ Realizar Novo Lançamento")

    with st.form("formulario_registro", clear_on_submit=True):
        data_registro = st.date_input("Data do Lançamento:", value=date.today())
        tipo = st.radio("Escolha a Operação:", ["Venda", "Gasto"], horizontal=True)
        valor = st.number_input("Valor (R$):", min_value=0.01, step=1.0, format="%.2f")
        pagamento = st.selectbox("Forma de Pagamento:", ["Dinheiro", "Pix", "Cartão de Débito", "Cartão de Crédito"])
        descricao = st.text_input("Descrição (Opcional):", placeholder="Ex: Venda de produto / Conta de luz")
        
        btn_salvar = st.form_submit_button("SALVAR REGISTRO")
        
        if btn_salvar:
            data_str = data_registro.strftime('%Y-%m-%d')
            data_formatada = data_registro.strftime('%d/%m/%Y')
            
            novo_item = {
                "data": data_str,
                "tipo": tipo,
                "valor": valor,
                "pagamento": pagamento,
                "descricao": descricao
            }
            supabase.table("lancamentos").insert(novo_item).execute()
            st.success(f"✅ {tipo} registrada com sucesso para {data_formatada}!")
            st.rerun()


# =========================================================
# TELA 2: LISTA DE LANÇAMENTOS (COM SELETOR NO CABEÇALHO)
# =========================================================
elif tela == "📋 Lista":
    st.subheader("📋 Lançamentos Cadastrados")
    
    # Caixa de seleção do dia NO CABEÇALHO
    data_selecionada = st.date_input(
        "📅 Selecione o dia para visualizar:", 
        value=date.today(), 
        key="data_filtro_lista"
    )
    data_str_lista = data_selecionada.strftime('%Y-%m-%d')
    data_fmt_lista = data_selecionada.strftime('%d/%m/%Y')

    st.divider()
    st.markdown(f"### Lançamentos de: **{data_fmt_lista}**")

    resposta = supabase.table("lancamentos").select("*").eq("data", data_str_lista).execute()
    df_lancamentos = pd.DataFrame(resposta.data)

    if df_lancamentos.empty:
        st.info(f"Nenhum lançamento cadastrado no dia {data_fmt_lista}.")
    else:
        for _, row in df_lancamentos.iterrows():
            icone = "🟢" if row['tipo'] == 'Venda' else "🔴"
            
            with st.expander(f"{icone} {row['tipo']}: R$ {float(row['valor']):.2f} ({row['pagamento']})"):
                st.write(f"**Descrição:** {row['descricao'] if row['descricao'] else 'Sem descrição'}")
                col1, col2 = st.columns(2)
                
                # Botão Apagar
                if col1.button("🗑️ Apagar", key=f"apagar_{row['id']}"):
                    supabase.table("lancamentos").delete().eq("id", row['id']).execute()
                    st.warning("Lançamento apagado!")
                    st.rerun()

                # Botão Corrigir Valor
                novo_val = col2.number_input("Corrigir Valor (R$):", value=float(row['valor']), key=f"valor_{row['id']}")
                if col2.button("💾 Atualizar", key=f"atualizar_{row['id']}"):
                    supabase.table("lancamentos").update({"valor": novo_val}).eq("id", row['id']).execute()
                    st.success("Valor corrigido!")
                    st.rerun()


# =========================================================
# TELA 3: FECHAMENTO DO DIA
# =========================================================
elif tela == "📊 Fechamento":
    st.subheader("📊 Fechamento do Dia")
    
    data_fechamento = st.date_input(
        "📅 Selecione a data do fechamento:", 
        value=date.today(), 
        key="data_filtro_fechamento"
    )
    data_str_fech = data_fechamento.strftime('%Y-%m-%d')
    data_fmt_fech = data_fechamento.strftime('%d/%m/%Y')

    st.divider()

    resposta_fechamento = supabase.table("lancamentos").select("*").eq("data", data_str_fech).execute()
    df_resumo = pd.DataFrame(resposta_fechamento.data)

    if not df_resumo.empty:
        vendas_totais = df_resumo[df_resumo['tipo'] == 'Venda']['valor'].sum()
        gastos_totais = df_resumo[df_resumo['tipo'] == 'Gasto']['valor'].sum()
        saldo_dia = vendas_totais - gastos_totais

        c1, c2 = st.columns(2)
        c1.metric("🟢 Vendas Totais (+)", f"R$ {vendas_totais:.2f}")
        c2.metric("🔴 Gastos Totais (-)", f"R$ {gastos_totais:.2f}")
        st.metric("💰 Saldo do Dia", f"R$ {saldo_dia:.2f}")

        st.divider()
        st.subheader("💳 Detalhamento de Valores")

        vendas_dinheiro = df_resumo[(df_resumo['pagamento'] == 'Dinheiro') & (df_resumo['tipo'] == 'Venda')]['valor'].sum()
        gastos_dinheiro = df_resumo[(df_resumo['pagamento'] == 'Dinheiro') & (df_resumo['tipo'] == 'Gasto')]['valor'].sum()
        gaveta_dinheiro = vendas_dinheiro - gastos_dinheiro

        pix = df_resumo[(df_resumo['pagamento'] == 'Pix') & (df_resumo['tipo'] == 'Venda')]['valor'].sum()
        debito = df_resumo[(df_resumo['pagamento'] == 'Cartão de Débito') & (df_resumo['tipo'] == 'Venda')]['valor'].sum()
        credito = df_resumo[(df_resumo['pagamento'] == 'Cartão de Crédito') & (df_resumo['tipo'] == 'Venda')]['valor'].sum()

        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.markdown("💵 **Dinheiro na Gaveta**")
            st.write(f"R$ {gaveta_dinheiro:.2f}")
        with col_p2:
            st.markdown("📱 **Total em Pix**")
            st.write(f"R$ {pix:.2f}")

        col_p3, col_p4 = st.columns(2)
        with col_p3:
            st.markdown("💳 **Cartão Débito**")
            st.write(f"R$ {debito:.2f}")
        with col_p4:
            st.markdown("💳 **Cartão Crédito**")
            st.write(f"R$ {credito:.2f}")
    else:
        st.info(f"Nenhum lançamento encontrado em {data_fmt_fech}.")


# =========================================================
# TELA 4: DEMONSTRATIVO MENSAL
# =========================================================
elif tela == "📅 Mensal":
    st.subheader("📅 Demonstrativo Mensal")

    col_m1, col_m2 = st.columns(2)
    meses_pt = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    
    mes_selecionado = col_m1.selectbox("Escolha o Mês:", meses_pt, index=date.today().month - 1)
    num_mes = meses_pt.index(mes_selecionado) + 1

    ano_atual = date.today().year
    ano_selecionado = col_m2.selectbox("Escolha o Ano:", list(range(ano_atual - 1, ano_atual + 3)), index=1)

    # Calcula o primeiro e o último dia do mês selecionado
    _, ultimo_dia = calendar.monthrange(ano_selecionado, num_mes)
    data_inicio = f"{ano_selecionado}-{num_mes:02d}-01"
    data_fim = f"{ano_selecionado}-{num_mes:02d}-{ultimo_dia:02d}"

    # Consulta filtrando do dia 01 até o último dia do mês
    resposta_mensal = (
        supabase.table("lancamentos")
        .select("*")
        .gte("data", data_inicio)
        .lte("data", data_fim)
        .execute()
    )
    df_mensal = pd.DataFrame(resposta_mensal.data)

    st.divider()

    if not df_mensal.empty:
        vendas_m = df_mensal[df_mensal['tipo'] == 'Venda']['valor'].sum()
        gastos_m = df_mensal[df_mensal['tipo'] == 'Gasto']['valor'].sum()
        saldo_m = vendas_m - gastos_m

        cm1, cm2 = st.columns(2)
        cm1.metric("🟢 Vendas no Mês (+)", f"R$ {vendas_m:.2f}")
        cm2.metric("🔴 Gastos no Mês (-)", f"R$ {gastos_m:.2f}")
        st.metric("💰 Resultado Líquido do Mês", f"R$ {saldo_m:.2f}")

        st.divider()
        st.subheader("🗓️ Resumo Dia a Dia")
        
        df_tabela = df_mensal.copy()
        df_tabela['data_fmt'] = pd.to_datetime(df_tabela['data']).dt.strftime('%d/%m/%Y')
        
        df_resumo_dias = df_tabela.groupby(['data_fmt', 'tipo'])['valor'].sum().unstack(fill_value=0).reset_index()
        if 'Venda' not in df_resumo_dias.columns: df_resumo_dias['Venda'] = 0.0
        if 'Gasto' not in df_resumo_dias.columns: df_resumo_dias['Gasto'] = 0.0
        
        df_resumo_dias['Saldo (R$)'] = df_resumo_dias['Venda'] - df_resumo_dias['Gasto']
        df_resumo_dias.rename(columns={'data_fmt': 'Data', 'Venda': 'Vendas (R$)', 'Gasto': 'Gastos (R$)'}, inplace=True)
        
        st.dataframe(df_resumo_dias[['Data', 'Vendas (R$)', 'Gastos (R$)', 'Saldo (R$)']], use_container_width=True)
    else:
        st.info(f"Nenhum lançamento encontrado em {mes_selecionado} de {ano_selecionado}.")

# =========================================================
# BARRA DE NAVEGAÇÃO FIXA NO RODAPÉ DO CELULAR
# =========================================================
with st.bottom:
    escolha_inferior = st.radio(
        label="Navegação",
        options=OPCOES_NAVEGACAO,
        index=OPCOES_NAVEGACAO.index(st.session_state.tela_ativa),
        horizontal=True,
        label_visibility="collapsed",
        key="barra_navegacao_bottom"
    )
    
    if escolha_inferior != st.session_state.tela_ativa:
        st.session_state.tela_ativa = escolha_inferior
        st.rerun()