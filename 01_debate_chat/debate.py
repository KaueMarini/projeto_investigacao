import os
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"

import streamlit as st
import sys
import re
import time
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from crewai_tools import SerperDevTool


st.set_page_config(page_title="DEBATE CHAT LIVE: Fly Automação", page_icon="⚖️", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    .stChatMessage { border-radius: 15px; border: 1px solid #30363d; margin-bottom: 15px; }
</style>
""", unsafe_allow_html=True)


class StreamolitLogger:
    def __init__(self, widget):
        self.widget = widget
        self.buffer = ""
    def write(self, text):
        text_clean = re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', text)
        self.buffer += text_clean
        self.widget.code(self.buffer[-1500:], language="bash")
    def flush(self): pass

class DebateManager:
    def __init__(self, openai_key, serper_key):
        os.environ["OPENAI_API_KEY"] = openai_key
        os.environ["SERPER_API_KEY"] = serper_key
        
        
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.8
        )
        self.search_tool = SerperDevTool()

    def gerar_dialogo(self, tema, historico, rodada):
        dom = Agent(
            role='Economista Libertário',
            goal='Defender o livre mercado e a desestatização total.',
            backstory="Você é o DOM. Capitalista ferrenho, irônico e focado em eficiência privada. Use frases curtas e ácidas.",
            llm=self.llm, tools=[self.search_tool], verbose=True, allow_delegation=False
        )

        che = Agent(
            role='Sociólogo Progressista',
            goal='Defender o bem-estar social e a intervenção do Estado para reduzir desigualdades.',
            backstory="Você é o CHE. Humanista, focado em justiça social e direitos coletivos. Responda ao Dom com firmeza moral.",
            llm=self.llm, tools=[self.search_tool], verbose=True, allow_delegation=False
        )

        task_dialogo = Task(
            description=f"""
            TEMA DO DEBATE: {tema}
            RODADA: {rodada}
            
            HISTÓRICO RECENTE: 
            {historico}
            
            MISSÃO:
            1. DOM fala primeiro, provocando ou respondendo ao histórico.
            2. CHE rebate o argumento do DOM imediatamente.
            3. REGRAS: Mantenha as mensagens CURTAS e DINÂMICAS (estilo chat). 
            
            FORMATO OBRIGATÓRIO:
            DOM: [Texto do Dom]
            CHE: [Texto do Che]
            """,
            expected_output="O diálogo exato entre DOM e CHE.",
            agent=dom
        )

        crew = Crew(agents=[dom, che], tasks=[task_dialogo], verbose=True)
        return crew.kickoff()

    def julgar_dialogo(self, dialogo_atual):
        athena = Agent(
            role='Mediadora de IA',
            goal='Analisar se o debate chegou ao fim ou se deve continuar.',
            backstory="Você é ATHENA. Deusa da Sabedoria. Analise a lógica e decida o status do debate.",
            llm=self.llm, verbose=True, allow_delegation=False
        )

        task_veredito = Task(
            description=f"Analise: '{dialogo_atual}'. O debate chegou a um CONSENSO, está em STALEMATE (travado) ou deve CONTINUE?",
            expected_output="Palavra-chave (CONSENSO, STALEMATE ou CONTINUE) e uma explicação de 1 frase.",
            agent=athena
        )

        crew = Crew(agents=[athena], tasks=[task_veredito], verbose=True)
        return crew.kickoff()


with st.sidebar:
    st.image("https://api.dicebear.com/7.x/bottts/svg?seed=Fly", width=80)
    st.title("Fly Automação: Debate PRO")
    openai_key = st.text_input("OpenAI API Key", value="xxx.xxx.xxx.xxx.xxxx", type="password")
    serper_key = st.text_input("Serper API Key", value="xxx.xxx.xxx.xxx.xxxx", type="password")
    
    st.divider()
    if st.button("Resetar Arena", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.rodada = 0
        st.session_state.status = "PRONTO"
        st.rerun()


if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "rodada" not in st.session_state: st.session_state.rodada = 0
if "status" not in st.session_state: st.session_state.status = "PRONTO"

st.title("⚖️ Arena Fly: O Grande Debate")
st.caption("Agentes Autônomos (CrewAI + GPT-4o) em um duelo de ideologias.")


for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"], avatar=msg["avatar"]):
        st.markdown(msg["content"])


if st.session_state.status == "PRONTO":
    tema = st.chat_input("Insira o tema do debate e veja a mágica acontecer...")
    if tema:
        if not openai_key:
            st.error("Coloque a sua Chave da OpenAI na lateral!")
        else:
            st.session_state.tema = tema
            st.session_state.status = "RODANDO"
            st.session_state.chat_history.append({"role": "user", "avatar": "👤", "content": f"**Tema da Rodada:** {tema}"})
            st.rerun()


if st.session_state.status == "RODANDO":
    st.session_state.rodada += 1
    
    with st.expander(f"🧠 Log de Processamento (Rodada {st.session_state.rodada})", expanded=True):
        log_placeholder = st.empty()
        logger = StreamolitLogger(log_placeholder)
        sys.stdout = logger 

        try:
            manager = DebateManager(openai_key, serper_key)
            
            
            historico_recente = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.chat_history[-4:] if m['role'] in ['DOM', 'CHE']])
            
            resultado = manager.gerar_dialogo(st.session_state.tema, historico_recente, st.session_state.rodada)
            dialogo_raw = str(resultado)
            
           
            if "DOM:" in dialogo_raw and "CHE:" in dialogo_raw:
                fala_dom = dialogo_raw.split("DOM:")[1].split("CHE:")[0].strip()
                fala_che = dialogo_raw.split("CHE:")[1].strip()
                
                st.session_state.chat_history.append({"role": "DOM", "avatar": "🟦", "content": fala_dom})
                st.session_state.chat_history.append({"role": "CHE", "avatar": "🟥", "content": fala_che})
            
            
            veredito = str(manager.julgar_dialogo(dialogo_raw))
            st.session_state.chat_history.append({"role": "ATHENA", "avatar": "⚖️", "content": f"**Veredito:** {veredito}"})

            
            if "CONSENSO" in veredito.upper() or "STALEMATE" in veredito.upper():
                st.session_state.status = "FIM"
            else:
                time.sleep(2) 
                st.rerun()

        except Exception as e:
            st.error(f"Erro na execução: {e}")
            st.session_state.status = "ERRO"
        
        finally:
            sys.stdout = sys.__stdout__

if st.session_state.status == "FIM":
    st.success("Debate finalizado com sucesso!")
