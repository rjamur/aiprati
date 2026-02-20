"""
Serviços de IA para o bot de cursos
"""
import requests
import os
import logging
from .scraper import buscar_cursos_por_termo, formatar_cursos_para_resposta

logger = logging.getLogger(__name__)


def processar_mensagem_cursos(conteudo_mensagem, historico_conversa=None):
    """
    Processa mensagem do usuário e retorna resposta sobre cursos
    """
    
    # Dicionário de palavras-chave para busca
    palavras_busca = {
        'engenharia': 'engenharia',
        'administração': 'administração',
        'administracao': 'administração',
        'pedagogia': 'pedagogia',
        'educação': 'educação',
        'educacao': 'educação',
        'tecnologia': 'tecnologia',
        'tecnólogo': 'tecnólogo',
        'tecnologico': 'tecnólogo',
        'saúde': 'saúde',
        'saude': 'saúde',
        'direito': 'direito',
        'contabil': 'contabilidade',
        'marketing': 'marketing',
        'gestão': 'gestão',
        'gestao': 'gestão',
        'design': 'design',
        'arte': 'arte',
        'história': 'história',
        'historia': 'história',
        'matemática': 'matemática',
        'matematica': 'matemática',
        'língua': 'língua',
        'lingua': 'língua',
        'português': 'português',
        'portugues': 'português',
        'inglês': 'inglês',
        'ingles': 'inglês',
        'física': 'física',
        'fisica': 'física',
        'química': 'química',
        'quimica': 'química',
        'biologia': 'biologia',
        'psicologia': 'psicologia',
        'enfermagem': 'enfermagem',
        'farmácia': 'farmácia',
        'farmacia': 'farmácia',
        'nutrição': 'nutrição',
        'nutricao': 'nutrição',
        # Adicionado suporte para AdS
        'ads': 'análise e desenvolvimento de sistemas',
        'analise e desenvolvimento': 'análise e desenvolvimento de sistemas',
        'desenvolvimento de sistemas': 'análise e desenvolvimento de sistemas',
        'sistemas': 'análise e desenvolvimento de sistemas',
        'programação': 'análise e desenvolvimento de sistemas',
        'programacao': 'análise e desenvolvimento de sistemas',
    }
    
    msg_lower = conteudo_mensagem.lower()
    
    # Busca genérica "que cursos vocês têm"
    if any(palavra in msg_lower for palavra in ['cursos', 'formações', 'cursos disponível', 'opção de curso']):
        if any(palavra in msg_lower for palavra in ['qual', 'quais', 'que', 'todos', 'todas']):
            # Retornar todos os cursos agrupados
            from .models import Curso
            bacharelado = Curso.objects.filter(tipo='bacharelado').count()
            licenciatura = Curso.objects.filter(tipo='licenciatura').count()
            tecnologico = Curso.objects.filter(tipo='tecnologico').count()
            
            resposta = f"""🎓 **Bem-vindo à Unifatecie!**

Oferecemos mais de 100 cursos de Graduação EAD:

📚 **Bacharelado** ({bacharelado} cursos)
📖 **Licenciatura** ({licenciatura} cursos)  
⚙️ **Tecnólogo** ({tecnologico} cursos)

Qual área você se interessa? Por exemplo:
• Engenharia
• Administração
• Educação
• Saúde
• Tecnologia
• Design
• Gestão

Ou digite o nome do curso que procura! 🔍"""
            return resposta
    
    # Buscar por palavra-chave
    for palavra, termo in palavras_busca.items():
        if palavra in msg_lower:
            cursos = buscar_cursos_por_termo(termo)
            if cursos.exists():
                return formatar_cursos_para_resposta(cursos)
    
    # Se não encontrou por palavra-chave, usar IA para entender melhor
    return gerar_resposta_com_ia(conteudo_mensagem, historico_conversa)


def gerar_resposta_com_ia(conteudo_mensagem, historico_conversa=None):
    """
    Usa OpenRouter/IA para gerar resposta personalizada
    """
    api_key = os.environ.get('OPENROUTER_API_KEY')
    if not api_key:
        return "Desculpe, não consegui processar sua mensagem no momento. Entre em contato com nosso time de atendimento."
    
    # Formar contexto com histórico se disponível
    contexto = ""
    if historico_conversa and len(historico_conversa) > 1:
        contexto += "\n\nHistórico da conversa:\n"
        for msg in historico_conversa[-5:]:  # Últimas 5 mensagens
            contexto += f"{msg['tipo']}: {msg['conteudo']}\n"
        contexto += "\nPergunta atual: " + conteudo_mensagem
    else:
        contexto = conteudo_mensagem
    
    try:
        resposta = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "https://api.aiprati.com.br",
            },
            json={
                "model": os.environ.get("OPENROUTER_MODEL", "deepseek/deepseek-chat"),
                "messages": [
                    {
                        "role": "system",
                        "content": """Você é um assistente de vendas de cursos de graduação EAD de uma faculdade chamada Unifatecie.
                        
Suas responsabilidades:
1. Ajudar potenciais alunos a encontrar cursos de interesse
2. Fornecer informações sobre duração, tipo (Bacharelado, Licenciatura, Tecnólogo)
3. Incentivar a inscrição
4. Ser amigável, profissional e respeitoso
5. Considerar o contexto da conversa para dar respostas mais personalizadas

Não mencione valores ou promoções específicas, apenas direcione para o formulário de matrícula.
Sempre termine com uma pergunta para manter o diálogo.
Responda sempre em português brasileiro."""
                    },
                    {
                        "role": "user",
                        "content": contexto
                    }
                ],
            },
            timeout=10
        )
        
        if resposta.status_code == 200:
            return resposta.json()["choices"][0]["message"]["content"]
        else:
            logger.error(f"Erro na API OpenRouter: {resposta.status_code}")
            return "Desculpe, estou reorganizando meus pensamentos. Tente novamente em alguns instantes! 🤔"
    
    except requests.RequestException as e:
        logger.error(f"Erro ao chamar IA: {e}")
        return "Desculpe, não consegui processar sua mensagem no momento. Nosso time de atendimento está disponível para ajudar!"
