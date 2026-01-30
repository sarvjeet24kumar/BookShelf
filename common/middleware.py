import logging
import time
from django.http import JsonResponse
from django.urls import resolve
from django.urls.exceptions import Resolver404
from common.logging_utils import (
    generate_request_id,
    set_request_id,
    set_tenant_id,
)
from tenants.context import get_current_tenant

logger = logging.getLogger(__name__)


class RequestIDMiddleware:
    """
    Middleware to generate or extract correlation IDs for request tracing.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        request_id = request.headers.get('X-Request-ID') or generate_request_id()
        
        set_request_id(request_id)
        request.request_id = request_id
        
        response = self.get_response(request)
        response['X-Request-ID'] = request_id
        return response


class RequestLogMiddleware:
    """
    Middleware for structured request/response logging.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        start_time = time.time()
        
        response = self.get_response(request)
        
        tenant = get_current_tenant()
        if tenant:
            set_tenant_id(str(tenant.id))
        

        execution_time_ms = int((time.time() - start_time) * 1000)
    
        if response.status_code < 400:
            logger.info(
                f"{request.method} {request.path} {response.status_code} ({execution_time_ms}ms)"
            )
        elif response.status_code < 500:
            logger.warning(
                f"{request.method} {request.path} {response.status_code} ({execution_time_ms}ms)"
            )
        else:
            logger.error(
                f"{request.method} {request.path} {response.status_code} ({execution_time_ms}ms)",
                exc_info=True
            )
        
        return response


class API404Middleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            resolve(request.path_info)
        except Resolver404:
            if request.path_info.startswith("/api/"):
                return JsonResponse(
                    {
                        "success": False,
                        "error": {
                            "code": "ENDPOINT_NOT_FOUND",
                            "message": "API endpoint does not exist",
                        },
                    },
                    status=404,
                )

        return self.get_response(request)
