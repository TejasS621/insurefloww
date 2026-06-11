"""Main backend API route registrations."""

from .admin_router import admin_router
from .application_router import application_router
from .auth_router import auth_router
from .health_router import health_router
from .payment_router import payment_router
from .policy_router import policy_router
from .provider_sync_router import provider_sync_router
from .quote_router import quote_router
from .ticket_router import ticket_router

