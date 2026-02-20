"""
Bot Unificado - Resposta simples e direta para todas as mensagens
"""
import json
import logging
import requests
import os
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from .models import Message

logger = logging.getLogger(__name__)


def enviar_para_chatwoot(conversation_id, account_id, text):
    """Envia mensagem para o Chatwoot usando o token do Agent Bot"""
    try:
        url = f"https://chat.aiprati.com.br/api/v1/accounts/{account_id}/conversations/{conversation_id}/messages"
        # Usar o token do Agent Bot "Bot Facul" para que a mensagem seja enviada como bot
        # e não como um agente humano (isso garante que o Chatwoot encaminhe para o WhatsApp)
        bot_token = os.environ.get('CHATWOOT_BOT_TOKEN', 'LptzThPMMHWzMnqcERJvdwoL')
        headers = {
            'api_access_token': bot_token,
            'Content-Type': 'application/json'
        }
        payload = {
            'content': text,
            'message_type': 'outgoing',
            'private': False
        }
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        logger.info(f"Chatwoot response status: {response.status_code}, body: {response.text}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Erro ao enviar para Chatwoot: {e}")
        return None


def assign_to_admin(conversation_id, account_id, admin_id):
    """Atribui conversa para admin"""
    try:
        url = f"https://chat.aiprati.com.br/api/v1/accounts/{account_id}/conversations/{conversation_id}/assignments"
        headers = {
            'api_access_token': os.environ.get('CHATWOOT_API_TOKEN', 'EvZGb4rPXHH3ccLEiNmoSDLq'),
            'Content-Type': 'application/json'
        }
        payload = {'assignee_id': admin_id}
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Erro ao assignar para admin: {e}")
        return None


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def webhook_unified(request):
    """
    Bot Unificado - Super simples, responde a tudo
    """
    try:
        data = json.loads(request.body)
        
        event = data.get('event')
        message_type = data.get('message_type')
        conversation = data.get('conversation', {}) or {}
        conversation_id = conversation.get('id')
        status = conversation.get('status')
        account_id = data.get('account', {}).get('id')
        content = (data.get('content') or '').strip()

        # Só processar mensagens incoming
        if event != 'message_created' or message_type != 'incoming':
            return JsonResponse({'status': 'ignored', 'reason': 'not_incoming'})

        # Verificar dados básicos
        if not conversation_id or not account_id or not content:
            return JsonResponse({'status': 'ignored', 'reason': 'missing_data'})

        # Só responder se status open/pending
        if status not in ('open', 'pending'):
            return JsonResponse({'status': 'ignored', 'reason': f'status_{status}'})

        content_lower = content.lower()
        
        # Transferir para humano se pedido explicitamente
        if any(palavra in content_lower for palavra in ['humano', 'atendente', 'pessoa']):
            admin_id = os.environ.get('CHATWOOT_ADMIN_ID', '1')
            assign_to_admin(conversation_id, account_id, admin_id)
            enviar_para_chatwoot(conversation_id, account_id, "Transferindo para um humano...")
            return JsonResponse({'status': 'success', 'action': 'handoff'})

        # Salvar mensagem
        Message.objects.create(
            conversation_id=str(conversation_id),
            channel='chatwoot',
            sender='user',
            text=content
        )

        # Gerar resposta baseada no conteúdo
        resposta = gerar_resposta_unificada(content, conversation_id)

        # Salvar resposta
        Message.objects.create(
            conversation_id=str(conversation_id),
            channel='chatwoot',
            sender='bot',
            text=resposta
        )

        # Enviar para Chatwoot
        enviar_para_chatwoot(conversation_id, account_id, resposta)
        
        return JsonResponse({'status': 'success', 'bot': 'unified'})

    except Exception as e:
        logger.error(f"Erro no bot unificado: {e}")
        return JsonResponse({'status': 'error', 'reason': str(e)}, status=500)


def gerar_resposta_unificada(content, conversation_id):
    """
    Gera resposta baseada no conteúdo da mensagem
    """
    content_lower = content.lower()
    
    # Detectar números de WhatsApp/telefone
    import re
    phone_patterns = [
        r'\b(\d{10,11})\b',  # 11999999999 ou 1199999999
        r'\((\d{2})\)\s*(\d{4,5})-?(\d{4})',  # (11) 99999-9999
        r'(\d{2})\s*(\d{4,5})-?(\d{4})',  # 11 99999-9999
    ]
    
    phone_found = False
    for pattern in phone_patterns:
        if re.search(pattern, content):
            phone_found = True
            break
    
    # Detectar emails
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    email_found = re.search(email_pattern, content)
    
    # Se forneceu WhatsApp ou email
    if phone_found or email_found:
        contact_type = "WhatsApp" if phone_found else "email"
        contact_value = content.strip()
        return f"""🎉 **Perfeito! Recebi seu {contact_type}: {contact_value}**

✅ **Próximos passos:**
1. Nossa equipe vai entrar em contato em até 2 horas
2. Vamos tirar todas suas dúvidas
3. Explicar valores e descontos especiais
4. Fazer sua matrícula online se quiser

🎓 **Enquanto isso, posso te ajudar com mais alguma dúvida?**
• Outros cursos que te interessam
• Formas de pagamento
• Processo de EAD
• Mercado de trabalho

**Nossa equipe especializada vai te ligar em breve!** 📞

Obrigado por escolher a Unifatecie! 🚀"""

    # Saudações
    elif any(palavra in content_lower for palavra in ['oi', 'olá', 'ola', 'bom dia', 'boa tarde', 'boa noite']):
        return """👋 Olá! Sou o assistente da Unifatecie!

Como posso ajudar você hoje?
• Informações sobre cursos
• Valores e matrículas
• Dúvidas sobre EAD

Me fala o que você precisa! 😊"""

    # Perguntas sobre TECNÓLOGOS especificamente
    elif any(palavra in content_lower for palavra in ['tecnólogo', 'tecnologo', 'tecnologos', 'tecnólogos']):
        return """⚙️ **Cursos Tecnólogos da Unifatecie (2-3 anos)**

**🖥️ Tecnologia da Informação:**
• Análise e Desenvolvimento de Sistemas (AdS)
• Redes de Computadores
• Segurança da Informação
• Gestão da TI

**💼 Gestão e Negócios:**
• Gestão Comercial
• Gestão de Recursos Humanos
• Gestão Financeira
• Logística
• Marketing

**🏗️ Engenharia e Produção:**
• Gestão da Produção Industrial
• Processos Gerenciais
• Gestão da Qualidade

**🎨 Design e Comunicação:**
• Design Gráfico
• Publicidade e Propaganda

**💰 Vantagens dos Tecnólogos:**
• Duração: 2 a 3 anos
• Foco prático e profissionalizante
• Entrada rápida no mercado
• Mensalidades a partir de R$ 99,90

📞 **Quer se matricular?** Me passa seu WhatsApp!"""

    # Perguntas sobre CURSOS CURTOS/MENOR DURAÇÃO
    elif any(palavra in content_lower for palavra in ['curto', 'curta', 'curtos', 'menor duração', 'rápido', 'rapidos']):
        return """⏱️ **Cursos Mais Curtos da Unifatecie**

**🥇 TECNÓLOGOS (2 a 2,5 anos):**
• **AdS - Análise e Desenvolvimento de Sistemas** (2,5 anos)
• **Gestão Comercial** (2 anos)
• **Gestão de RH** (2 anos)
• **Marketing** (2 anos)
• **Design Gráfico** (2 anos)
• **Logística** (2 anos)

**🥈 LICENCIATURAS (3 anos):**
• **Pedagogia** (3 anos)
• **Letras** (3 anos)
• **História** (3 anos)
• **Matemática** (3 anos)

**💡 Por que escolher um curso mais curto?**
• Formação rápida
• Entrada antecipada no mercado
• Mensalidades mais acessíveis
• Foco prático

**🎯 Mais procurados:**
1. AdS (programação/desenvolvimento)
2. Gestão Comercial (vendas/negócios)
3. Pedagogia (educação)

📞 **Qual te interessa?** Me fala seu WhatsApp que nossa equipe explica tudo!"""

    # Perguntas sobre AdS especificamente
    elif any(palavra in content_lower for palavra in ['ads', 'análise', 'desenvolvimento', 'sistemas', 'programação']):
        return """🖥️ **AdS - Análise e Desenvolvimento de Sistemas**

**📋 Sobre o curso:**
• **Duração:** 2,5 anos (5 semestres)
• **Modalidade:** 100% EAD
• **Tipo:** Tecnólogo
• **Reconhecido pelo MEC**

**💻 O que você vai aprender:**
• Programação (Python, Java, JavaScript)
• Desenvolvimento Web e Mobile
• Banco de Dados
• Análise de Sistemas
• Gestão de Projetos
• Cybersegurança

**🚀 Mercado de trabalho:**
• Desenvolvedor de Sistemas
• Programador
• Analista de Sistemas
• Desenvolvedor Web/Mobile
• Salários: R$ 3.500 a R$ 8.000+

**💰 Investimento:**
• A partir de R$ 99,90/mês
• Bolsas e descontos disponíveis
• Material digital incluído

📞 **Quer se matricular em AdS?** Me passa seu WhatsApp!"""

    # Perguntas sobre MARKETING especificamente
    elif 'marketing' in content_lower:
        return """📈 **Marketing - Tecnólogo**

**📋 Sobre o curso:**
• **Duração:** 2 anos (4 semestres)
• **Modalidade:** 100% EAD
• **Tipo:** Tecnólogo
• **Reconhecido pelo MEC**

**🎯 O que você vai aprender:**
• Marketing Digital e Redes Sociais
• Publicidade e Propaganda
• Pesquisa de Mercado
• Comportamento do Consumidor
• Estratégias de Vendas
• Branding e Comunicação
• E-commerce e Marketing Online
• Análise de Dados e Métricas

**💼 Mercado de trabalho:**
• Analista de Marketing
• Coordenador de Marketing Digital
• Especialista em Redes Sociais
• Gerente de Produto
• Consultor de Marketing
• Salários: R$ 2.500 a R$ 6.000+

**💰 Investimento:**
• A partir de R$ 149,90/mês
• Desconto na 1ª mensalidade
• Material digital incluído

📞 **Quer se matricular em Marketing?** Me passa seu WhatsApp!"""

    # Perguntas sobre ADMINISTRAÇÃO especificamente
    elif any(palavra in content_lower for palavra in ['administração', 'administracao', 'adm']):
        return """💼 **Administração - Bacharelado**

**📋 Sobre o curso:**
• **Duração:** 4 anos (8 semestres)
• **Modalidade:** 100% EAD
• **Tipo:** Bacharelado
• **Reconhecido pelo MEC**

**📊 O que você vai aprender:**
• Gestão Empresarial
• Recursos Humanos
• Finanças Corporativas
• Marketing e Vendas
• Logística e Operações
• Empreendedorismo
• Liderança e Negociação
• Planejamento Estratégico

**🏢 Mercado de trabalho:**
• Administrador
• Gerente Geral
• Consultor Empresarial
• Analista de Negócios
• Empreendedor
• Salários: R$ 3.000 a R$ 10.000+

**💰 Investimento:**
• A partir de R$ 199,90/mês
• Facilitações de pagamento
• Material digital incluído

📞 **Quer se matricular em Administração?** Me passa seu WhatsApp!"""

    # Perguntas sobre PEDAGOGIA especificamente
    elif 'pedagogia' in content_lower:
        return """👩‍🏫 **Pedagogia - Licenciatura**

**📋 Sobre o curso:**
• **Duração:** 3 anos (6 semestres)
• **Modalidade:** 100% EAD
• **Tipo:** Licenciatura
• **Reconhecido pelo MEC**

**📚 O que você vai aprender:**
• Psicologia da Educação
• Didática e Metodologias
• Gestão Escolar
• Educação Inclusiva
• Alfabetização e Letramento
• Psicopedagogia
• Tecnologias Educacionais
• Avaliação Educacional

**🎓 Mercado de trabalho:**
• Professor de Educação Infantil
• Professor dos Anos Iniciais
• Coordenador Pedagógico
• Orientador Educacional
• Gestor Escolar
• Salários: R$ 2.500 a R$ 5.500+

**💰 Investimento:**
• A partir de R$ 119,90/mês
• Desconto para professores
• Material digital incluído

📞 **Quer se matricular em Pedagogia?** Me passa seu WhatsApp!"""

    # Perguntas sobre ENGENHARIA especificamente
    elif 'engenharia' in content_lower:
        return """🏗️ **Engenharias - Bacharelado**

**📋 Cursos disponíveis:**
• **Engenharia Civil** (5 anos)
• **Engenharia Elétrica** (5 anos)
• **Engenharia de Produção** (5 anos)
• **Engenharia Mecânica** (5 anos)
• **Engenharia de Software** (4 anos)

**⚙️ O que você vai aprender:**
• Cálculos e Física Aplicada
• Projetos e Desenvolvimento
• Gestão de Obras/Processos
• Tecnologias Avançadas
• Sustentabilidade
• Inovação e Pesquisa

**🔧 Mercado de trabalho:**
• Engenheiro de Projetos
• Gerente de Obras
• Consultor Técnico
• Empreendedor do setor
• Pesquisador
• Salários: R$ 4.000 a R$ 15.000+

**💰 Investimento:**
• A partir de R$ 299,90/mês
• Laboratórios virtuais
• Material técnico incluído

📞 **Qual engenharia te interessa?** Me passa seu WhatsApp!"""

    # Perguntas sobre GESTÃO DE RH especificamente
    elif any(palavra in content_lower for palavra in ['rh', 'recursos humanos', 'gestão de pessoas']):
        return """👥 **Gestão de Recursos Humanos - Tecnólogo**

**📋 Sobre o curso:**
• **Duração:** 2 anos (4 semestres)
• **Modalidade:** 100% EAD
• **Tipo:** Tecnólogo
• **Reconhecido pelo MEC**

**💡 O que você vai aprender:**
• Recrutamento e Seleção
• Treinamento e Desenvolvimento
• Gestão de Desempenho
• Folha de Pagamento e Benefícios
• Relações Trabalhistas
• Clima Organizacional
• Coaching e Liderança
• Psicologia Organizacional

**🤝 Mercado de trabalho:**
• Analista de RH
• Especialista em R&S
• Business Partner
• Consultor de RH
• Coordenador de Pessoas
• Salários: R$ 2.800 a R$ 7.000+

**💰 Investimento:**
• A partir de R$ 149,90/mês
• Área em alta demanda
• Material digital incluído

📞 **Quer se matricular em Gestão de RH?** Me passa seu WhatsApp!"""

    # Perguntas sobre cursos gerais
    elif any(palavra in content_lower for palavra in ['curso', 'cursos', 'graduação', 'graduacao', 'formação', 'engenharia', 'administração', 'pedagogia']):
        return """🎓 **Cursos da Unifatecie**

Oferecemos mais de 100 cursos EAD:

📚 **Bacharelado (4-5 anos)** - Administração, Engenharia, Direito...
📖 **Licenciatura (3-4 anos)** - Pedagogia, Matemática, História...
⚙️ **Tecnólogo (2-3 anos)** - AdS, Gestão, Marketing...

**🔥 Principais áreas:**
• **Tecnologia:** AdS, Redes, Segurança
• **Gestão:** Administração, RH, Marketing
• **Engenharia:** Civil, Elétrica, Produção
• **Educação:** Pedagogia, Licenciaturas
• **Saúde:** Enfermagem, Farmácia

**⚡ Mais procurados:**
1. AdS (Tecnólogo - 2,5 anos)
2. Administração (Bacharelado - 4 anos)  
3. Pedagogia (Licenciatura - 3 anos)

📞 **Quer detalhes de algum específico?** Me fala qual curso te interessa!"""

    # Perguntas sobre preços/valores
    elif any(palavra in content_lower for palavra in ['preço', 'valor', 'quanto', 'custa', 'tabela', 'mensalidade']):
        return """💰 **Valores e Formas de Pagamento**

**💸 Faixas de preço:**
• **Tecnólogos:** R$ 99,90 a R$ 199,90/mês
• **Licenciaturas:** R$ 119,90 a R$ 249,90/mês
• **Bacharelados:** R$ 149,90 a R$ 399,90/mês

**🎁 Facilidades:**
• **50% OFF** na 1ª mensalidade
• Desconto para pagamento à vista
• Parcelamento no cartão
• **FIES** e **ProUni** disponíveis
• Material digital **GRATUITO**
• Sem taxa de matrícula

**📊 Exemplos:**
• AdS: R$ 149,90/mês
• Pedagogia: R$ 119,90/mês
• Administração: R$ 199,90/mês

📞 **Quer um orçamento personalizado?** 
Me passa seu WhatsApp que nossa equipe prepara uma proposta especial!"""

    # Interesse em matrícula ou palavras de interesse
    elif any(palavra in content_lower for palavra in ['quero', 'gostaria', 'matricula', 'inscrever', 'começar', 'interesse', 'interessado', 'me inscrever']):
        return """🚀 **Que ótimo! Vamos começar sua matrícula!**

**📝 Para agilizar, me passa:**
📱 **Seu WhatsApp:** [seu número]
📧 **Ou seu email:** [seu email]

**🎯 Nossa equipe vai:**
• Ligar em até 2 horas
• Tirar todas suas dúvidas  
• Explicar valores e descontos
• Fazer sua matrícula online

**⚡ Ou se preferir:**
• Ligue: 0800-xxx-xxxx
• Site: unifatecie.edu.br

**📚 Qual curso te interessa mais?**
• AdS (Tecnólogo - 2,5 anos)
• Marketing (Tecnólogo - 2 anos)
• Administração (Bacharelado - 4 anos)
• Pedagogia (Licenciatura - 3 anos)

Estamos aqui para realizar seu sonho! 🎯"""

    # Resposta genérica (melhorada)
    else:
        return f"""😊 Vi que você quer saber sobre: "{content}"

🎓 **A Unifatecie oferece:**
• **+100 cursos EAD** reconhecidos pelo MEC
• **Valores a partir de R$ 99,90/mês**
• **Diploma válido** em todo território nacional
• **Suporte acadêmico** completo

**🔍 Me diga o que procura:**
• "quais tecnólogos" → Lista cursos de 2-3 anos
• "cursos curtos" → Opções de menor duração  
• "AdS" → Análise e Desenvolvimento
• "preços" → Valores e facilidades
• "quero me matricular" → Processo de inscrição

📞 **Ou me fala seu WhatsApp** que nossa equipe liga pra você!"""