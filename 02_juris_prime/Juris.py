import os
import asyncio
import chainlit as cl
from pypdf import PdfReader
from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI


OPENAI_API_KEY = "xxx.xxx.xx.xxx.xxx.xxxxx"
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY


llm = ChatOpenAI(model="gpt-4o", temperature=0.75)

def extract_text_from_pdf(file_path):
    """Extrai texto do PDF de forma limpa."""
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            content = page.extract_text()
            if content: text += content + "\n"
        return text[:12000] 
    except Exception as e:
        return f"Erro na leitura: {e}"

@cl.on_chat_start
async def start():
    cl.user_session.set("debate_ativo", True)
    
    
    magnus = Agent(
        role='Sócio Sênior Estrategista',
        goal='Desenvolver a narrativa de defesa macro e princípios constitucionais.',
        backstory="Dr. Magnus. Veterano da advocacia. Prefere teses robustas e boa-fé.",
        llm=llm
    )
    lexia = Agent(
        role='Processualista Técnica',
        goal='Identificar nulidades de rito, vícios de forma e erros de prazo.',
        backstory="Dra. Lexia. Cirúrgica com a letra da lei. Não tolera erros formais.",
        llm=llm
    )
    rivals = Agent(
        role='Promotor de Ataque',
        goal='Destruir a estratégia da defesa e apontar a responsabilidade do réu.',
        backstory="Promotor Rivals. Perspicaz em encontrar contradições lógicas.",
        llm=llm
    )

    cl.user_session.set("equipe", [
        (magnus, "⚖️ DR. MAGNUS", "Sócio Sênior"),
        (lexia, "📚 DRA. LEXIA", "Especialista Processual"),
        (rivals, "😈 PROMOTOR RIVALS", "Simulador de Acusação")
    ])

   
    files = await cl.AskFileMessage(
        content="⚖️ **JURIS PRIME: MODO DEBATE PROFISSIONAL**\nAnexe o PDF para iniciarmos a banca. Para parar, digite **'para'**.",
        accept=["application/pdf"]
    ).send()
    
    case_text = extract_text_from_pdf(files[0].path)
    cl.user_session.set("case_text", case_text)
    cl.user_session.set("historico", "O debate técnico começou.")

    await cl.Message(content="⚖️ **A banca está reunida e os advogados iniciaram a análise.**").send()
    
    
    await rodar_debate()

async def rodar_debate():
    while cl.user_session.get("debate_ativo"):
        equipe = cl.user_session.get("equipe")
        case_text = cl.user_session.get("case_text")
        historico = cl.user_session.get("historico")

        for agente, nome, cargo in equipe:
            if not cl.user_session.get("debate_ativo"):
                break

          
            task = Task(
                description=f"""
                --- DOCUMENTO BASE DO CASO ---
                {case_text}
                
                --- HISTÓRICO DAS ÚLTIMAS FALAS (CONTEXTO) ---
                {historico}
                
                SUA MISSÃO COMO {nome}:
                1. Analise o caso e o que seus colegas disseram acima.
                2. Desenvolva um argumento jurídico sólido de 2 a 3 parágrafos.
                3. PROIBIÇÃO: Não repita artigos ou argumentos que já foram citados no histórico.
                4. AVANÇO: Se o Magnus falou de nulidade, você deve falar de outro aspecto (ex: provas, mérito, dolo).
                5. INTERAÇÃO: Concorde ou discorde frontalmente do colega anterior antes de trazer sua tese.
                """,
                expected_output="Um comentário jurídico denso, inédito e bem fundamentado.",
                agent=agente
            )

            crew = Crew(agents=[agente], tasks=[task])
            result = await cl.make_async(crew.kickoff)()

          
            header = f"### {nome}\n**Cargo:** _{cargo}_"
            corpo_mensagem = f"{header}\n\n---\n\n{result.raw}"
            
            await cl.Message(content=corpo_mensagem, author=nome).send()
            
            
            historico += f"\n\n[{nome}]: {result.raw}"
          
            historico_linhas = historico.split("\n\n")[-5:] 
            cl.user_session.set("historico", "\n\n".join(historico_linhas))
            
            
            await asyncio.sleep(10)

@cl.on_message
async def on_message(message: cl.Message):
    if message.content.lower() in ["para", "parar", "stop", "chega", "exit"]:
        cl.user_session.set("debate_ativo", False)
        await cl.Message(content="🛑 **DEBATE ENCERRADO.** A banca finalizou os trabalhos.").send()
