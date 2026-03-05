import streamlit as st
import pandas as pd
import re
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Orçador de Telas", page_icon="🦟", layout="centered")

# --- 1. DADOS E LINKS ---
LINKS_PRODUTO = {
    65.00: "https://www.mercadolivre.com.br/tela-mosquiteira-em-fibra-de-vidro-pedidos-personalizados/up/MLBU3738817132",
    70.00: "https://www.mercadolivre.com.br/tela-mosquiteira-em-fibra-de-vidro-pedidos-personalizados/up/MLBU3729810893",
    75.00: "https://www.mercadolivre.com.br/tela-mosquiteira-em-fibra-de-vidro-pedidos-personalizados/up/MLBU3738817986",
    78.00: "https://www.mercadolivre.com.br/tela-mosquiteira-em-fibra-de-vidro-pedidos-personalizados/up/MLBU3738817984",
    130.00: "https://www.mercadolivre.com.br/tela-mosquiteira-em-fibra-de-vidro-pedidos-personalizados/up/MLBU3738815224",
    150.00: "https://www.mercadolivre.com.br/tela-mosquiteira-em-fibra-de-vidro-pedidos-personalizados/up/MLBU3738817128",
    180.00: "https://www.mercadolivre.com.br/tela-mosquiteira-em-fibra-de-vidro-pedidos-personalizados/up/MLBU3738817982",
    200.00: "https://www.mercadolivre.com.br/tela-mosquiteira-em-fibra-de-vidro-pedidos-personalizados/up/MLBU3738817130"
}

# --- 2. CARREGAR TABELA ---
@st.cache_data
def carregar_tabela():
    try:
        df = pd.read_excel("tabela_mosquiteira_formatada.xlsx", index_col=0)
        df.index = df.index.astype(float)
        df.columns = df.columns.astype(float)
        return df
    except Exception as e:
        return pd.DataFrame()

df_precos = carregar_tabela()

# --- 3. FUNÇÕES ---
def saudacao():
    hora = datetime.now().hour
    if 5 <= hora < 12: return "Bom dia"
    elif 12 <= hora < 18: return "Boa tarde"
    else: return "Boa noite"

def extrair_medidas_avancado(texto):
    texto = texto.lower()
    # Normalize separadores (' e ', quebra de linha)
    texto = re.sub(r'\s+e\s+', '|', texto)
    texto = texto.replace('\n', '|')
    # O PULO DO GATO: Só usa vírgula como separador se tiver um espaço DEPOIS dela.
    # Assim, 140,50 não quebra, mas "140x100, 50x50" quebra.
    texto = re.sub(r',\s+', '|', texto)
    
    padrao_medida = r'(\d+[.,]?\d*)\s*[xX*]\s*(\d+[.,]?\d*)'
    blocos = texto.split('|')
    itens_encontrados = []
    
    for bloco in blocos:
        bloco = bloco.strip()
        if not bloco: continue
        
        match_medida = re.search(padrao_medida, bloco)
        if match_medida:
            l_raw, a_raw = match_medida.groups()
            
            # Textos para cálculo com ponto
            l_str_math = l_raw.replace(',', '.')
            a_str_math = a_raw.replace(',', '.')
            
            # Procura a quantidade
            texto_sem_medida = bloco.replace(match_medida.group(0), '')
            match_qtd = re.search(r'\b(\d+)\b', texto_sem_medida)
            qtd = int(match_qtd.group(1)) if match_qtd else 1
            
            l_calc = float(l_str_math)
            a_calc = float(a_str_math)
            
            # --- INTELIGÊNCIA DE EXIBIÇÃO ---
            # Se for > 4, consideramos que o cliente já digitou em centímetros (ex: 140,50)
            if l_calc > 4:
                l_show = l_raw # Mantém do jeito que o cliente digitou (com vírgula/ponto)
                l_calc /= 100  # Converte o cálculo interno para metros
            else:
                # Se digitou em metros (ex: 1.2), converte o visual para cm redondinho (120)
                l_show = str(int(l_calc * 100))
                
            if a_calc > 4:
                a_show = a_raw
                a_calc /= 100
            else:
                a_show = str(int(a_calc * 100))
                
            itens_encontrados.append({
                'qtd': qtd, 
                'l': l_calc, 
                'a': a_calc, 
                'l_show': l_show, 
                'a_show': a_show
            })
            
    return itens_encontrados

def buscar_preco(largura, altura):
    medidas = sorted([largura, altura])
    menor, maior = medidas[0], medidas[1]
    if menor > 1.50 or maior > 3.00: return None
    try:
        # Pega a primeira coluna/linha que seja MAIOR ou IGUAL à medida (Arredonda sempre pra cima na tabela)
        col = df_precos.columns[df_precos.columns >= (menor - 0.0001)].min()
        lin = df_precos.index[df_precos.index >= (maior - 0.0001)].min()
        return df_precos.loc[lin, col]
    except:
        return None

# --- 4. INTERFACE ---
st.title("🦟 Orçador Mercado Livre")

if st.button("Limpar Tela"):
    st.session_state.pergunta_input = ""

pergunta = st.text_area("Cole a pergunta do cliente:", height=120, key="pergunta_input", placeholder="Ex: 1 tela 140,50x110,39...")

if st.button("Gerar Resposta 🚀", type="primary", use_container_width=True):
    if not pergunta:
        st.warning("Cole a pergunta primeiro!")
    else:
        itens = extrair_medidas_avancado(pergunta)
        
        if not itens:
            st.error("Não entendi as medidas. Tente o formato: 140x120")
        else:
            linhas_orcamento = []
            blocos_links = []
            total_geral = 0
            qtd_total_telas = sum(item['qtd'] for item in itens)
            
            for item in itens:
                preco_unit = buscar_preco(item['l'], item['a'])
                l_show = item['l_show']
                a_show = item['a_show']
                qtd = item['qtd']
                
                if preco_unit:
                    preco_total_item = preco_unit * qtd
                    total_geral += preco_total_item
                    
                    if qtd > 1:
                        linhas_orcamento.append(f"• {qtd} telas de {l_show}cm x {a_show}cm: R$ {preco_total_item:.2f} (R$ {preco_unit:.2f} cada)")
                    else:
                        linhas_orcamento.append(f"• Tela ({l_show}cm x {a_show}cm): R$ {preco_unit:.2f}")
                    
                    link = LINKS_PRODUTO.get(preco_unit, "Link indisponível")
                    
                    blocos_links.append(
                        f"\n🔴 LINK PARA MEDIDA {l_show}x{a_show}:\n"
                        f"ATENÇÃO!!! Adicione {qtd} UNIDADE(S) da variação de [R$ {preco_unit:.2f}] no carrinho.\n"
                        f"Link: {link}"
                    )
                else:
                    linhas_orcamento.append(f"• {qtd} telas de {l_show}cm x {a_show}cm: ⚠️ Medida excede limite de envio")

            # Montagem do Cabeçalho
            if qtd_total_telas > 1:
                cabecalho = f"O custo para a produção fica no total de R$ {total_geral:.2f}:\n"
            else:
                cabecalho = "" # Se for 1 tela, não repete o valor no topo.
            
            texto_final = (
                f"{saudacao()}! Tudo bem?\n\n"
                f"{cabecalho}"
                f"{chr(10).join(linhas_orcamento)}\n\n"
                f"Caso tenha interesse, seguem os links para compra:\n"
                f"{''.join(blocos_links)}\n\n"
                f"(Após a compra vou te chamar pelo chat da compra para registrar a produção do seu pedido) Qualquer dúvida estou à disposição!Obrigada"
            )
            
            st.success("Orçamento Gerado!")
            st.code(texto_final, language=None)
