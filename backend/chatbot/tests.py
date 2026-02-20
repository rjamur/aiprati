from django.test import TestCase, override_settings
from unittest.mock import patch, MagicMock
from .services import get_ai_response
from .models import Message

# Helper class to simulate the Message model without hitting the database
class MockMessage:
    def __init__(self, sender, text):
        self.sender = sender
        self.text = text

@override_settings(GEMINI_API_KEY="fake-gemini-key-for-testing")
class GetAIResponseTests(TestCase):

    @patch('chatbot.services.genai')
    def test_get_ai_response_success(self, mock_genai):
        """
        Testa se get_ai_response chama a API do Gemini e retorna o texto com sucesso.
        """
        # 1. Arrange: Configura a cadeia de mocks para a API do Gemini
        mock_response = MagicMock()
        mock_response.text = 'Esta é uma resposta mockada do Gemini.'

        mock_chat = MagicMock()
        mock_chat.send_message.return_value = mock_response

        mock_model = MagicMock()
        mock_model.start_chat.return_value = mock_chat

        mock_genai.GenerativeModel.return_value = mock_model

        # Cria um histórico de conversa falso
        conversation_history = [
            MockMessage(sender='user', text='Olá!'),
            MockMessage(sender='bot', text='Olá! Como posso ajudar?'),
            MockMessage(sender='user', text='Qual o endereço?'),
        ]

        # 2. Act: Executa a função que está sendo testada
        response_text = get_ai_response(conversation_history)

        # 3. Assert: Verifica se o resultado é o esperado e se os mocks foram chamados
        self.assertEqual(response_text, "Esta é uma resposta mockada do Gemini.")
        mock_genai.configure.assert_called_once_with(api_key="fake-gemini-key-for-testing")
        mock_genai.GenerativeModel.assert_called_once()
        mock_model.start_chat.assert_called_once()
        # Verifica se a última mensagem do usuário foi corretamente enviada
        mock_chat.send_message.assert_called_once_with('Qual o endereço?')

    @patch('chatbot.services.genai.GenerativeModel')
    def test_get_ai_response_api_error(self, mock_generative_model):
        """
        Testa o comportamento de get_ai_response quando a API do Gemini lança uma exceção.
        """
        # 1. Arrange: Configura o mock para levantar uma exceção
        mock_generative_model.side_effect = Exception("Erro de conexão simulado com Gemini")

        conversation_history = [MockMessage(sender='user', text='Isso vai dar erro?')]

        # 2. Act: Executa a função
        response_text = get_ai_response(conversation_history)

        # 3. Assert: Verifica se a mensagem de erro amigável foi retornada
        expected_error_message = "Desculpe, estou com problemas para me conectar com minha inteligência. Tente novamente mais tarde."
        self.assertEqual(response_text, expected_error_message)
