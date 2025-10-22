"""
Сервисный модуль для отправки email сообщений.

Обеспечивает централизованное управление отправкой email, обработку ошибок
и единообразное форматирование сообщений.
"""

import logging
from typing import Optional, Dict, Any

from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


class EmailService:
    """
    Сервис для отправки email сообщений.
    
    Предоставляет методы для отправки различных типов email:
    - верификация email
    - уведомления
    - транзакционные сообщения
    """
    
    @staticmethod
    def send_verification_email(
        user_email: str, 
        verification_url: str,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Отправляет email для подтверждения адреса.
        
        Args:
            user_email: Email адрес получателя
            verification_url: URL для подтверждения email
            context: Дополнительный контекст для шаблона
            
        Returns:
            bool: True если отправка успешна, False в случае ошибки
        """
        try:
            # Подготавливаем контекст для шаблона
            email_context = {
                'verification_url': verification_url,
                'user_email': user_email,
                'site_name': getattr(settings, 'SITE_NAME', 'Handmade Marketplace'),
                **(context or {})
            }
            
            # Рендерим текстовую и HTML версии письма
            subject = _('Подтверждение email адреса')
            text_message = render_to_string(
                'users/emails/email_verification.txt', 
                email_context
            )
            html_message = render_to_string(
                'users/emails/email_verification.html', 
                email_context
            )
            
            # Отправляем email
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user_email],
                reply_to=[getattr(settings, 'SUPPORT_EMAIL', 'support@handmade-marketplace.ru')]
            )
            email.attach_alternative(html_message, "text/html")
            
            sent_count = email.send(fail_silently=False)
            
            logger.info(
                f"Verification email sent to {user_email}. "
                f"Message ID: {getattr(email, 'message_id', 'N/A')}"
            )
            
            return sent_count > 0
            
        except Exception as e:
            logger.error(
                f"Failed to send verification email to {user_email}. "
                f"Error: {str(e)}",
                exc_info=True
            )
            return False
    
    @staticmethod
    def send_welcome_email(user_email: str, user_name: str = None) -> bool:
        """
        Отправляет приветственное письмо после успешной регистрации.
        
        Args:
            user_email: Email адрес получателя
            user_name: Имя пользователя (опционально)
            
        Returns:
            bool: True если отправка успешна, False в случае ошибки
        """
        try:
            context = {
                'user_email': user_email,
                'user_name': user_name,
                'site_name': getattr(settings, 'SITE_NAME', 'Handmade Marketplace'),
            }
            
            subject = _('Добро пожаловать в Handmade Marketplace!')
            text_message = render_to_string('users/emails/welcome_email.txt', context)
            html_message = render_to_string('users/emails/welcome_email.html', context)
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user_email]
            )
            email.attach_alternative(html_message, "text/html")
            
            sent_count = email.send(fail_silently=False)
            
            logger.info(f"Welcome email sent to {user_email}")
            return sent_count > 0
            
        except Exception as e:
            logger.error(f"Failed to send welcome email to {user_email}. Error: {str(e)}")
            return False
    
    @staticmethod
    def send_notification(
        user_email: str,
        subject: str,
        template_name: str,
        context: Dict[str, Any]
    ) -> bool:
        """
        Универсальный метод для отправки уведомлений.
        
        Args:
            user_email: Email адрес получателя
            subject: Тема письма
            template_name: Имя шаблона (без расширения)
            context: Контекст для шаблона
            
        Returns:
            bool: True если отправка успешна, False в случае ошибки
        """
        try:
            base_context = {
                'site_name': getattr(settings, 'SITE_NAME', 'Handmade Marketplace'),
                'support_email': getattr(settings, 'SUPPORT_EMAIL', 'support@handmade-marketplace.ru'),
            }
            context = {**base_context, **context}
            
            text_message = render_to_string(f'{template_name}.txt', context)
            html_message = render_to_string(f'{template_name}.html', context)
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user_email]
            )
            email.attach_alternative(html_message, "text/html")
            
            sent_count = email.send(fail_silently=False)
            
            logger.info(f"Notification '{subject}' sent to {user_email}")
            return sent_count > 0
            
        except Exception as e:
            logger.error(
                f"Failed to send notification to {user_email}. "
                f"Subject: {subject}. Error: {str(e)}"
            )
            return False


# Создаем экземпляр сервиса для удобного импорта
email_service = EmailService()