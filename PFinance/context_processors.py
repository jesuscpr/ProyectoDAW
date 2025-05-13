from django.db.models import Count, Q, Prefetch
from django.contrib.auth.models import User

from PFinance.models import Alert


def alerts_context(request):
    if not request.user.is_authenticated:
        return {}

    user_with_alerts = User.objects.filter(pk=request.user.pk).prefetch_related(
        Prefetch(
            'alerts',
            queryset=Alert.objects.order_by('-created_at')[:5],
            to_attr='recent_alerts'
        )
    ).annotate(
        unread_count=Count('alerts', filter=Q(alerts__read=False))
    ).first()

    return {
        'unread_count': user_with_alerts.unread_count,
        'recent_alerts': user_with_alerts.recent_alerts,
        'usuario': user_with_alerts.profile
    }