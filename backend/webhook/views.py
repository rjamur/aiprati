import json
import logging
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)

@csrf_exempt
@require_POST
def chatwoot_webhook(request):
    """
    Recebe e processa eventos do webhook do Chatwoot.
    """
    try:
        payload = json.loads(request.body)
        event_type = payload.get('event')

        logger.info(f"Webhook event '{event_type}' received.")
        logger.debug(json.dumps(payload, indent=2, ensure_ascii=False))

        return JsonResponse({"status": "ok"}, status=200)
    except json.JSONDecodeError:
        logger.warning("Received invalid JSON in webhook.")
        return HttpResponse("Invalid JSON", status=400)
    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        return HttpResponse("Internal Server Error", status=500)
