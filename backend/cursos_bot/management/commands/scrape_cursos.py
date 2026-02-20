from django.core.management.base import BaseCommand
from cursos_bot.scraper import scrape_cursos


class Command(BaseCommand):
    help = 'Scrape cursos do site da Unifatecie'

    def handle(self, *args, **options):
        self.stdout.write('Iniciando scraping de cursos...')
        
        sucesso = scrape_cursos()
        
        if sucesso:
            self.stdout.write(
                self.style.SUCCESS('✅ Scraping concluído com sucesso!')
            )
        else:
            self.stdout.write(
                self.style.ERROR('❌ Erro ao fazer scraping dos cursos')
            )
