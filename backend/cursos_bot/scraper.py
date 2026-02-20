"""
Web scraper para baixar cursos do site unifatecie.edu.br
"""
import requests
from bs4 import BeautifulSoup
from django.db import transaction
from .models import Curso
import logging

logger = logging.getLogger(__name__)


def scrape_cursos():
    """
    Faz scraping dos cursos do site da Unifatecie
    """
    url = "https://unifatecie.edu.br/site/cursos-graduacao-ead/"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Erro ao acessar {url}: {e}")
        return False

    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Encontrar todas as tabelas com cursos
    tables = soup.find_all('table')
    
    if not tables:
        logger.warning("Nenhuma tabela encontrada na página")
        return False

    cursos_salvos = 0
    
    with transaction.atomic():
        for table in tables:
            rows = table.find_all('tr')[1:]  # Pula header
            
            for row in rows:
                cells = row.find_all('td')
                
                # A tabela tem 4 colunas: nome | nome (repetido) | duração | tipo
                if len(cells) < 4:
                    continue
                
                try:
                    nome = cells[0].get_text(strip=True)
                    duracao = cells[2].get_text(strip=True)
                    tipo = cells[3].get_text(strip=True).lower()
                    
                    if not nome or not duracao:
                        continue
                    
                    # Mapear tipos
                    tipo_map = {
                        'licenciatura': 'licenciatura',
                        'bacharelado': 'bacharelado',
                        'tecnólogo': 'tecnologico',
                        'tecnológico': 'tecnologico',
                    }
                    
                    tipo_mapeado = tipo_map.get(tipo, 'bacharelado')
                    
                    # Criar ou atualizar curso
                    curso, created = Curso.objects.update_or_create(
                        nome=nome,
                        defaults={
                            'tipo': tipo_mapeado,
                            'duracao': duracao,
                        }
                    )
                    
                    if created:
                        cursos_salvos += 1
                        logger.info(f"Novo curso criado: {nome}")
                
                except (IndexError, AttributeError) as e:
                    logger.error(f"Erro ao processar linha da tabela: {e}")
                    continue
    
    logger.info(f"Scraping concluído. {cursos_salvos} novos cursos salvos.")
    return True


def buscar_cursos_por_termo(termo):
    """
    Busca cursos por termo (nome ou tipo)
    """
    termo_lower = termo.lower()
    
    # Buscar por nome
    cursos = Curso.objects.filter(nome__icontains=termo_lower)
    
    # Se não encontrou, buscar por tipo
    if not cursos.exists():
        tipo_map = {
            'bach': 'bacharelado',
            'lic': 'licenciatura',
            'tecn': 'tecnologico',
        }
        
        for chave, tipo in tipo_map.items():
            if chave in termo_lower:
                cursos = Curso.objects.filter(tipo=tipo)
                break
    
    return cursos


def formatar_cursos_para_resposta(cursos):
    """
    Formata uma lista de cursos para resposta de chat
    """
    if not cursos:
        return "Desculpe, não encontramos cursos que correspondem à sua busca. 😟\n\nTemos mais de 100 cursos de Graduação EAD! Digite 'que cursos vocês têm' para ver todas as opções."
    
    resposta = "📚 **Cursos Encontrados:**\n\n"
    
    for curso in cursos[:10]:  # Limitar a 10 resultados
        resposta += f"• **{curso.nome}**\n"
        resposta += f"  📖 Tipo: {curso.get_tipo_display()}\n"
        resposta += f"  ⏱️  Duração: {curso.duracao}\n\n"
    
    if cursos.count() > 10:
        resposta += f"... e mais {cursos.count() - 10} cursos!\n\n"
    
    resposta += "💡 Quer mais informações sobre algum curso específico?"
    
    return resposta
