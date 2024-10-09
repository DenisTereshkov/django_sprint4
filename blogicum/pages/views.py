import enum

from django.shortcuts import render


class ErrorStatus(enum.Enum):
    """Enum описание ошибок"""

    error404 = 404
    error403 = 403
    error500 = 500


def page_not_found(request, exception):
    """Функция для ошибки 404"""
    return render(request, 'pages/404.html', status=ErrorStatus.error404.value)


def csrf_failure(request, reason=''):
    """Функция для ошибки 403"""
    return render(
        request,
        'pages/403csrf.html',
        status=ErrorStatus.error403.value
    )


def server_error(request):
    """Функция для ошибки 500"""
    return render(request, 'pages/500.html', status=ErrorStatus.error500.value)
