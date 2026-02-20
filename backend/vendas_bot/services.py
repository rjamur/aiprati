"""
Services para processamento de mensagens e captura de leads
Integra funcionalidades do bot de cursos
"""
import logging
import re
from django.db import transaction
from .models import Lead, PricingInfo
import requests
import os

logger = logging.getLogger(__name__)
# Importar lógica do cursos_bot
try:
    from cursos_bot.services import processar_mensagem_cursos, gerar_resposta_com_ia
    from cursos_bot.scraper import buscar_cursos_por_termo, formatar_cursos_para_resposta
except ImportError:
    logger.warning("Cursos_bot não disponível - usando fallback")
    processar_mensagem_cursos = None

def extrair_email_telefone(mensagem):
    """
    Extrai email e telefone da mensagem usando regex
    """
    # Regex para email
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', mensagem)
    email = email_match.group(0) if email_match else None
    
    # Regex para telefone (várias formatos)
    telefone_patterns = [
        r'\(?(\d{2})\)?\s?(\d{4,5})-?(\d{4})',  # (11) 99999-9999 ou (11) 9999-9999
        r'(\d{10,11})',  # 11999999999 ou 1199999999
    ]
    
    telefone = None
    for pattern in telefone_patterns:
        match = re.search(pattern, mensagem)
        if match:
            telefone = ''.join(match.groups())
            break
    
    return email, telefone


def criar_lead(nome, mensagem, curso_interesse=None, email=None, telefone=None):
    """
    Cria novo lead a partir da mensagem do usuário
    """
    # Extrair dados se não fornecidos
    if not email or not telefone:
        msg_email, msg_telefone = extrair_email_telefone(mensagem)
        email = email or msg_email
        telefone = telefone or msg_telefone
    
    with transaction.atomic():
        lead = Lead.objects.create(
            nome=nome,
            email=email,
            telefone=telefone,
            curso_interesse=curso_interesse,
            mensagem_original=mensagem[:500],  # Limitar para 500 chars
            status='novo',
            prioridade=1,  # Média por padrão
        )
        
        logger.info(f"Novo lead criado: {lead.nome} ({lead.email or lead.telefone})")
        return lead


def detectar_pergunta_cursos(conteudo_mensagem):
    """
    Detecta se o usuário está perguntando sobre cursos
    """
    conteudo_lower = conteudo_mensagem.lower()
    palavras_chave_cursos = [
        'cursos', 'formações', 'curso', 'graduação', 'bacharelado', 'licenciatura', 'tecnólogo', 
        'área', 'qual', 'quais', 'qual área', 'que curso', 'se oferecem', 'vocês têm',
        'ads', 'análise e desenvolvimento de sistemas', 'desenvolvimento de sistemas',
        'administração', 'engenharia', 'pedagogia', 'direito', 'enfermagem', 'psicologia'
    ]
    
    return any(palavra in conteudo_lower for palavra in palavras_chave_cursos)


def processar_pergunta_cursos(conteudo_mensagem, historico_conversa=None):
    """
    Processa perguntas sobre cursos usando a lógica do cursos_bot
    """
    try:
        # Importar dinamicamente para evitar circular imports
        from cursos_bot.services import processar_mensagem_cursos
        
        resposta = processar_mensagem_cursos(conteudo_mensagem, historico_conversa)
        
        # Adicionar informação de contato ao final
        resposta += "\n\n📞 Quer se matricular? Deixe seu telefone ou email para um atendente entrar em contato!"
        
        return resposta
    except Exception as e:
        logger.error(f"Erro ao processar pergunta de cursos: {e}")
        # Fallback para resposta genérica
        return """🎓 **Cursos Disponíveis**

A Unifatecie oferece mais de 100 cursos de Graduação EAD:

📚 **Bacharelado** - Formação completa em diversas áreas
📖 **Licenciatura** - Para quem quer se tornar professor
⚙️ **Tecnólogo** - Cursos técnicos de curta duração

Qual área você se interessa?
• Engenharia
• Administração  
• Educação
• Saúde
• Tecnologia
• Design
• Gestão

📞 Quer mais detalhes? Deixe seu telefone ou email!"""


def processar_mensagem_vendas(conteudo_mensagem, nome_usuario=None, email_usuario=None, telefone_usuario=None, historico_conversa=None):
    """
    Processa mensagem e retorna resposta de vendas
    Detecta intenção: dúvida sobre cursos, preço, informações, agendamento, etc
    """
    conteudo_lower = conteudo_mensagem.lower()
    
    # 1. Detectar se está perguntando sobre CURSOS (PRIORIDADE 1)
    se_pergunta_cursos = detectar_pergunta_cursos(conteudo_mensagem)
    
    # 2. Detectar se está perguntando sobre preço/valor
    se_pergunta_preco = any(palavra in conteudo_lower for palavra in ['preço', 'valor', 'quanto', 'custa', 'tabela', 'investimento', 'bolsa', 'financ'])
    
    # 3. Detectar se quer se matricular
    se_quer_matricular = any(palavra in conteudo_lower for palavra in ['quero', 'gostaria', 'matricul', 'inscrever', 'começar'])
    
    # 4. Detectar se quer agendar
    se_quer_agendar = any(palavra in conteudo_lower for palavra in ['quer', 'agendar', 'conversa', 'ligar', 'falar'])
    
    # Se detectou interesse, criar lead
    if se_quer_matricular or se_quer_agendar or email_usuario or telefone_usuario:
        lead = criar_lead(
            nome=nome_usuario or "Cliente Anônimo",
            mensagem=conteudo_mensagem,
            email=email_usuario,
            telefone=telefone_usuario
        )
    
    # Gerar resposta baseada na intenção (em ordem de prioridade)
    if se_pergunta_cursos:
        return processar_pergunta_cursos(conteudo_mensagem, historico_conversa)
    elif se_pergunta_preco:
        return gerar_resposta_preco(conteudo_mensagem, historico_conversa)
    elif se_quer_matricular or se_quer_agendar:
        return gerar_resposta_lead(conteudo_mensagem, historico_conversa)
    else:
        return gerar_resposta_ia(conteudo_mensagem, historico_conversa)


def gerar_resposta_preco(pergunta, historico_conversa=None):
    """
    Responde dúvidas sobre preço
    """
    pergunta_lower = pergunta.lower()
    
    # Buscar preços ativos
    precos = PricingInfo.objects.filter(ativo=True)[:5]
    
    if not precos.exists():
        return "Desculpe, informações de preço não estão disponíveis no momento. Entre em contato com nossos vendedores! 📞"
    
    resposta = "💰 **INFORMAÇÕES DE PREÇO**\n\n"
    
    # Se perguntou sobre curso específico
    for preco in precos:
        se_mencionou_curso = preco.curso_nome.lower() in pergunta_lower
        
        if se_mencionou_curso or precos.count() <= 3:
            valor_desconto = preco.valor_com_desconto() if preco.desconto_percentual > 0 else None
            
            resposta += f"**{preco.curso_nome}**\n"
            resposta += f"  💵 À vista: R$ {preco.valor_integral:,.2f}\n"
            
            if valor_desconto:
                resposta += f"  🎁 Com desconto: R$ {valor_desconto:,.2f}\n"
            
            resposta += f"  📅 {preco.parcelas}x de R$ {preco.valor_parcela:,.2f}\n\n"
    
    resposta += "📞 Quer saber mais ou se matricular? Deixe seu telefone ou email! ✉️"
    
    return resposta


def gerar_resposta_lead(pergunta, historico_conversa=None):
    """
    Responde leads interessados
    """
    return """✨ **Ótimo!** Estamos felizes com seu interesse! 

Para ajudá-lo melhor com a matrícula, precisamos de:
- 📞 Seu telefone/WhatsApp
- 📧 Seu melhor email
- 🎓 Qual curso você gostaria de cursar?

Você pode responder aqui mesmo ou falar diretamente com nosso time:
📱 **WhatsApp:** https://wa.me/554491751988
📧 **Email:** vendas@unifatecie.edu.br

Aguardamos seu contato! 🚀"""


def gerar_resposta_ia(pergunta, historico_conversa=None):
    """
    Usa OpenRouter para responder perguntas genéricas sobre vendas
    """
    openrouter_key = os.environ.get('OPENROUTER_API_KEY')
    openrouter_model = os.environ.get('OPENROUTER_MODEL', 'deepseek/deepseek-chat')
    
    if not openrouter_key:
        return "Desculpe, não conseguimos processar sua pergunta no momento. Entre em contato com nosso time! 📞"
    
    # Formar contexto com histórico se disponível
    contexto = ""
    if historico_conversa and len(historico_conversa) > 1:
        contexto += "\n\nHistórico da conversa:\n"
        for msg in historico_conversa[-5:]:  # Últimas 5 mensagens
            contexto += f"{msg['tipo']}: {msg['conteudo']}\n"
        contexto += "\nPergunta atual: " + pergunta
    else:
        contexto = pergunta
    
    system_prompt = """Você é um vendedor amigável e profissional de uma instituição de educação à distância (EAD).
    
Seu objetivo é:
1. Responder dúvidas sobre cursos e matrículas
2. Ser informativo e amigável
3. Incentivar o contato para mais informações
4. Mencionar números de contato ou WhatsApp quando apropriado
5. Considerar o contexto da conversa para dar respostas mais personalizadas

Sempre responda em português brasileiro de forma concisa (máximo 150 palavras)."""
    
    try:
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {openrouter_key}',
                'HTTP-Referer': 'https://api.aiprati.com.br',
                'Content-Type': 'application/json',
            },
            json={
                'model': openrouter_model,
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': contexto},
                ],
                'temperature': 0.7,
            },
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            logger.error(f"Erro OpenRouter: {response.status_code}")
            return "Desculpe, erro ao processar sua pergunta. Tente novamente! 🙏"
    
    except requests.RequestException as e:
        logger.error(f"Erro ao chamar OpenRouter: {e}")
        return "Desculpe, erro de conexão. Entre em contato direto com nosso time! 📞"
