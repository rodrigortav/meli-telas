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
    # 1. Normaliza separadores para dividir a frase em blocos lógicos
    texto = texto.lower()
    # Troca ' e ' por um separador único, assim como quebras de linha
    texto = re.sub(r'\s+e\s+', '|', texto)
    texto = texto.replace('\n', '|').replace(',', '|')
    
    blocos = texto.split('|')
    itens_encontrados = []
    
    # Regex para achar a medida (Largura x Altura)
    padrao_medida = r'(\d+[.,]?\d*)\s*[xX*]\s*(\d+[.,]?\d*)'
    
    for bloco in blocos:
        bloco = bloco.strip()
        if not bloco: continue
        
        # Procura se tem medida neste bloco
        match_medida = re.search(padrao_medida, bloco)
        
        if match_medida:
            l_raw, a_raw = match_medida.groups()
            
            # --- INTELIGÊNCIA DE QUANTIDADE ---
            # Remove a medida encontrada do texto para não confundir com quantidade
            # Ex: "2 telas de 60x60" -> remove "60x60" -> sobra "2 telas de "
            texto_sem_medida = bloco.replace(match_medida.group(0), '')
            
            # Procura um número isolado no que sobrou do texto
            match_qtd = re.search(r'\b(\d+)\b', texto_sem_medida)
            
            qtd = 1
            if match_qtd:
                qtd = int(match_qtd.group(1))
            
            # Converte medidas (cm -> m)
            l = float(l_raw.replace(',', '.'))
            a = float(a_raw.replace(',', '.'))
            if l > 4: l /= 100
            if a > 4: a /= 100
            
            itens_encontrados.append((qtd, l, a))
            
    return itens_encontrados

def buscar_preco(largura, altura):
    medidas = sorted([largura, altura])
    menor, maior = medidas[0], medidas[1]
    if menor > 1.50 or maior > 3.00: return None
    try:
        col = df_precos.columns[df_precos.columns >= menor].min()
        lin = df_precos.index[df_precos.index >= maior].min()
        return df_precos.loc[lin, col]
    except:
        return None

# --- 4. INTERFACE ---
st.title("🦟 Orçador Mercado Livre")
st.caption("Cole a pergunta do cliente abaixo:")

pergunta = st.text_area("Mensagem do Cliente:", height=100, label_visibility="collapsed", placeholder="Ex: 2 telas de 60x60 e 4 de 100x120...")

if st.button("Gerar Resposta 🚀", type="primary", use_container_width=True):
    if not pergunta:
        st.warning("Cole uma pergunta primeiro!")
    else:
        # Usa a nova função de extração
        itens = extrair_medidas_avancado(pergunta)
        
        if not itens:
            st.error("Não entendi as medidas. Tente separar por vírgula ou 'e'.")
        else:
            linhas_orcamento = []
            blocos_links = []
            total_geral = 0
            
            for i, (qtd, l, a) in enumerate(itens):
                preco_unitario = buscar_preco(l, a)
                l_cm, a_cm = int(l*100), int(a*100)
                
                if preco_unitario:
                    preco_total_item = preco_unitario * qtd
                    total_geral += preco_total_item
                    
                    # Formatação sem o "Tela 1, 2, 3..."
                    if qtd > 1:
                        linhas_orcamento.append(f"• {qtd} telas de {l_cm}cm x {a_cm}cm: R$ {preco_total_item:.2f} (R$ {preco_unitario:.2f} cada)")
                    else:
                        linhas_orcamento.append(f"• Tela {l_cm}cm x {a_cm}cm: R$ {preco_unitario:.2f}")
                    
                    link = LINKS_PRODUTO.get(preco_unitario, "Link indisponível")
                    
                    # Bloco de link também sem a numeração
                    bloco = (f"\n🔴 LINK PARA MEDIDA {l_cm}x{a_cm}:\n"
                             f"ATENÇÃO!!! Adicione {qtd} UNIDADE(S) da variação de [R$ {preco_unitario:.2f}] no carrinho.\n"
                             f"Link: {link}")
                    blocos_links.append(bloco)
                else:
                    linhas_orcamento.append(f"• {qtd} telas de {l_cm}cm x {a_cm}cm: ⚠️ Medida excede limite de envio")

            # Montagem da resposta final
            texto_final = (
                f"{saudacao()}! Tudo bem?\n\n"
                f"O valor total fica: R$ {total_geral:.2f}\n"
                f"{chr(10).join(linhas_orcamento)}\n\n"
                f"Caso tenha interesse, seguem os links para compra:\n"
                f"{''.join(blocos_links)}\n\n"
                f"Qualquer dúvida estou à disposição!"
            )
            
            st.success(f"Orçamento Gerado! Total: R$ {total_geral:.2f}")
            st.markdown("**Copie a resposta abaixo:**")
            st.code(texto_final, language=None)
