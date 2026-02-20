from django.db import models

class Message(models.Model):
    """
    Representa uma única mensagem em uma conversa, seja do usuário ou do bot.
    """
    channel = models.CharField(
        max_length=20,
        choices=[('telegram', 'Telegram'), ('twilio_whatsapp', 'Twilio WhatsApp'), ('chatwoot', 'Chatwoot')],
        help_text="Canal de origem da mensagem."
    )
    conversation_id = models.CharField(
        max_length=255,
        help_text="ID da conversa no canal de origem (ex: chat_id do Telegram, 'whatsapp:+...' do Twilio)."
    )
    sender = models.CharField(
        max_length=10,
        choices=[('user', 'Usuário'), ('bot', 'Bot')],
        help_text="Quem enviou a mensagem."
    )
    text = models.TextField(help_text="O conteúdo da mensagem.")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Data e hora de criação.")

    def __str__(self):
        return f"Msg de {self.sender} no canal {self.channel} ({self.conversation_id}) em {self.created_at.strftime('%d/%m %H:%M')}"

    class Meta:
        ordering = ['created_at']