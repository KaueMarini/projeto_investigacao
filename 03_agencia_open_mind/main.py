import os
import asyncio
import json
import chainlit as cl
from duckduckgo_search import DDGS
from langchain_openai import ChatOpenAI

# 1. CONFIGURAÇÃO DE CHAVES
# Substitua pela sua chave sk-...
OPENAI_API_KEY = "xxxx.x.xx.x.x.xxxx"
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

ARQUIVO_FINAL = "PROJETO_MARKETING_FINAL.md"


llm = ChatOpenAI(model="gpt-4o", temperature=0.8)

async def market_research(niche, phase):
    """Busca tendências reais para embasar os agentes."""
    query = f"{niche} tendências mercado {phase} 2026"
    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=3)]
            return results
    except:
        return []

async def agency_turn(agent, niche, phase, context, market_data):
    """Turno de fala de cada especialista da agência."""
    prompt = f"""
    VOCÊ É: {agent['name']} ({agent['role']})
    PROJETO: "{niche}"
    FASE ATUAL: {phase}
    
    DADOS DE MERCADO (PESQUISA REAL): 
    {json.dumps(market_data, indent=2)}
    
    HISTÓRICO DA REUNIÃO (O QUE JÁ FOI DITO):
    {context}
    
    SUA MISSÃO:
    1. Seja um especialista de elite. Use termos técnicos do seu cargo.
    2. DESENVOLVA: Escreva de 2 a 3 parágrafos densos com ideias práticas.
    3. NÃO REPITA: Se alguém já sugeriu algo, critique ou traga uma abordagem complementar inédita.
    4. INTERAJA: Responda diretamente ao colega que falou antes de você.
    5. ESTILO: {agent['style']}
    """
    
    try:
        response = await llm.ainvoke(prompt)
        return response.content.strip()
    except Exception as e:
        return f"*(O especialista {agent['name']} está revisando os dados...)*"

async def generate_final_doc(niche, history):
    """Compilação final feita pelo 'CEO' da Agência."""
    prompt = f"""
    ATUE COMO CEO DA AGÊNCIA OPEN-MIND.
    Gere o Book Estratégico Final para o cliente: "{niche}".
    
    HISTÓRICO COMPLETO DO DEBATE:
    {history}
    
    FORMATO (MARKDOWN):
    # 🚀 PLANEJAMENTO ESTRATÉGICO: {niche.upper()}
    ## 1. Posicionamento e Persona (Stratos)
    ## 2. Direção de Arte e Branding (Pixel)
    ## 3. Growth e Aquisição (Metric)
    ## 4. Cronograma de Execução (Next Steps)
    """
    try:
        res = await llm.ainvoke(prompt)
        return res.content.strip()
    except:
        return "Erro na compilação do documento final."

@cl.on_chat_start
async def start():
    # Configuração Visual dos Agentes
    try:
        await cl.Avatar(name="STRATOS", url="https://api.dicebear.com/7.x/avataaars/svg?seed=Stratos").send()
        await cl.Avatar(name="PIXEL", url="https://api.dicebear.com/7.x/avataaars/svg?seed=Pixel").send()
        await cl.Avatar(name="METRIC", url="https://api.dicebear.com/7.x/avataaars/svg?seed=Metric").send()
        await cl.Avatar(name="SISTEMA", url="https://api.dicebear.com/7.x/bottts/svg?seed=Fly").send()
    except: pass

    await cl.Message(
        content="🏢 **AGÊNCIA OPEN-MIND: OPENAI EDITION**\nO time de elite está na sala. \n\n**Qual ideia de negócio vamos transformar em realidade hoje?**",
        author="SISTEMA"
    ).send()
    
    res = await cl.AskUserMessage(content="", timeout=600).send()
    user_niche = res['output']
    
    history = [f"CLIENTE DESEJA LANÇAR: {user_niche}"]
    
    team = [
        {"name": "STRATOS", "emoji": "🧠", "role": "Estrategista de Marca", "style": "Foque no 'Porquê' e na dor do cliente."},
        {"name": "PIXEL", "emoji": "🎨", "role": "Diretor Criativo", "style": "Foque na 'Vibe', estética e diferenciação visual."},
        {"name": "METRIC", "emoji": "📊", "role": "Growth Hacker", "style": "Foque em 'Números', tráfego pago e ROI."}
    ]

    phases = [
        "FASE 1: Diagnóstico e Público-Alvo",
        "FASE 2: Branding e Conceito Criativo",
        "FASE 3: Estratégia de Vendas e Canais",
        "FASE 4: O Plano de Lançamento"
    ]

    for phase in phases:
        await cl.Message(content=f"📌 **{phase}**", author="SISTEMA").send()
        
        # Busca dados reais do mercado para a fase atual
        market_data = await market_research(user_niche, phase)
        
        for agent in team:
            # Gerenciamento de Memória (Últimas 5 mensagens)
            contexto_recente = "\n".join(history[-5:])
            
            msg_raw = await agency_turn(agent, user_niche, phase, contexto_recente, market_data)
            
            # Formatação Visual Premium
            msg_formatada = f"### {agent['emoji']} {agent['name']}\n**{agent['role']}**\n---\n{msg_raw}"
            
            await cl.Message(content=msg_formatada, author=agent['name']).send()
            
            history.append(f"{agent['name']}: {msg_raw}")
            await asyncio.sleep(6) # Pausa para leitura no vídeo

    # Finalização
    await cl.Message(content="✅ **REUNIÃO ENCERRADA.** Gerando o Book Estratégico...", author="SISTEMA").send()
    final_doc = await generate_final_doc(user_niche, "\n".join(history))
    
    with open(ARQUIVO_FINAL, "w", encoding="utf-8") as f:
        f.write(final_doc)
    
    await cl.Message(content=f"📄 **BOOK DO PROJETO ENTREGUE:**\n\n{final_doc}", author="SISTEMA").send()
