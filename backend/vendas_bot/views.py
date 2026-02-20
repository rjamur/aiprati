from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def webhook_vendas(request):
    return JsonResponse({"status": "ignored", "reason": "disabled_use_unified_bot"})

@csrf_exempt  
def webhook_debug(request):
    return JsonResponse({"status": "ignored", "reason": "disabled_use_unified_bot"})

def listar_leads(request):
    return JsonResponse({"leads": []})
