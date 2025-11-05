from fastapi import HTTPException
from typing import Optional
import logging

# Import wyjątków Supabase (z fallback jeśli struktura jest inna)
try:
    from supabase.exceptions import APIError as SupabaseAPIError
    from supabase.exceptions import AuthError as SupabaseAuthError
except ImportError:
    # Fallback dla różnych wersji biblioteki
    SupabaseAPIError = None
    SupabaseAuthError = None

# Import wyjątków OpenAI
try:
    from openai import APIError as OpenAIAPIError
    from openai import AuthenticationError as OpenAIAuthError
    from openai import RateLimitError as OpenAIRateLimitError
    from openai import APITimeoutError as OpenAITimeoutError
except ImportError:
    # Fallback dla różnych wersji biblioteki
    OpenAIAPIError = None
    OpenAIAuthError = None
    OpenAIRateLimitError = None
    OpenAITimeoutError = None

logger = logging.getLogger(__name__)


class ErrorHandler:
    """Centralna obsługa błędów z szczegółowym logowaniem i mapowaniem"""
    
    @staticmethod
    def handle_supabase_error(error: Exception, context: str = "") -> HTTPException:
        """
        Obsługuje błędy Supabase z szczegółowym mapowaniem
        
        Args:
            error: Wyjątek z Supabase
            context: Kontekst operacji (np. "login", "register")
        
        Returns:
            HTTPException z odpowiednim kodem i komunikatem
        """
        error_msg = str(error)
        error_type = type(error).__name__
        
        # Loguj szczegóły błędu
        logger.error(
            f"Supabase error in {context}: {error_type} - {error_msg}",
            extra={
                "error_type": error_type,
                "error_message": error_msg,
                "context": context,
                "full_error": str(error)
            }
        )
        
        # Mapowanie konkretnych błędów Supabase
        if SupabaseAuthError and isinstance(error, SupabaseAuthError):
            # Błędy autentykacji
            if "Invalid login credentials" in error_msg or "invalid_credentials" in error_msg.lower():
                return HTTPException(
                    status_code=401,
                    detail="Nieprawidłowy email lub hasło"
                )
            elif "Email not confirmed" in error_msg:
                return HTTPException(
                    status_code=403,
                    detail="Email nie został potwierdzony. Sprawdź swoją skrzynkę pocztową."
                )
            elif "User already registered" in error_msg or "already_registered" in error_msg.lower():
                return HTTPException(
                    status_code=409,
                    detail="Użytkownik o podanym emailu już istnieje"
                )
            elif "Password should be at least" in error_msg:
                return HTTPException(
                    status_code=400,
                    detail="Hasło jest za krótkie. Minimum 6 znaków."
                )
            elif "Invalid token" in error_msg or "token" in error_msg.lower():
                return HTTPException(
                    status_code=401,
                    detail="Nieprawidłowy lub wygasły token"
                )
            else:
                return HTTPException(
                    status_code=401,
                    detail=f"Błąd autentykacji: {error_msg}"
                )
        
        elif SupabaseAPIError and isinstance(error, SupabaseAPIError):
            # Błędy API Supabase
            status_code = getattr(error, 'code', 500)
            if status_code == 400:
                return HTTPException(
                    status_code=400,
                    detail=f"Nieprawidłowe żądanie: {error_msg}"
                )
            elif status_code == 404:
                return HTTPException(
                    status_code=404,
                    detail="Zasób nie został znaleziony"
                )
            elif status_code == 429:
                return HTTPException(
                    status_code=429,
                    detail="Zbyt wiele żądań. Spróbuj ponownie za chwilę."
                )
            else:
                return HTTPException(
                    status_code=500,
                    detail=f"Błąd serwisu autentykacji: {error_msg}"
                )
        
        # Ogólny błąd Supabase
        if "network" in error_msg.lower() or "connection" in error_msg.lower():
            return HTTPException(
                status_code=503,
                detail="Brak połączenia z serwisem autentykacji. Spróbuj ponownie później."
            )
        
        return HTTPException(
            status_code=500,
            detail=f"Błąd autentykacji: {error_msg}"
        )
    
    @staticmethod
    def handle_openai_error(error: Exception, context: str = "") -> str:
        """
        Obsługuje błędy OpenAI i zwraca komunikat do wyświetlenia użytkownikowi
        
        Args:
            error: Wyjątek z OpenAI
            context: Kontekst operacji
        
        Returns:
            String z komunikatem błędu
        """
        error_msg = str(error)
        error_type = type(error).__name__
        
        # Loguj szczegóły błędu
        logger.error(
            f"OpenAI error in {context}: {error_type} - {error_msg}",
            extra={
                "error_type": error_type,
                "error_message": error_msg,
                "context": context,
                "full_error": str(error)
            }
        )
        
        # Mapowanie konkretnych błędów OpenAI
        if OpenAIAuthError and isinstance(error, OpenAIAuthError):
            return "Nieprawidłowy klucz API OpenAI. Sprawdź czy klucz jest poprawny i aktywny."
        
        elif OpenAIRateLimitError and isinstance(error, OpenAIRateLimitError):
            return "Przekroczono limit żądań do OpenAI. Spróbuj ponownie za chwilę."
        
        elif OpenAITimeoutError and isinstance(error, OpenAITimeoutError):
            return "Timeout połączenia z OpenAI. Spróbuj ponownie."
        
        elif OpenAIAPIError and isinstance(error, OpenAIAPIError):
            status_code = getattr(error, 'status_code', None)
            if status_code == 400:
                return "Nieprawidłowe żądanie do OpenAI. Sprawdź parametry zapytania."
            elif status_code == 401:
                return "Brak autoryzacji do OpenAI. Sprawdź klucz API."
            elif status_code == 429:
                return "Zbyt wiele żądań do OpenAI. Spróbuj ponownie za chwilę."
            elif status_code == 500:
                return "Błąd serwera OpenAI. Spróbuj ponownie później."
            else:
                return f"Błąd OpenAI API: {error_msg}"
        
        # Ogólny błąd OpenAI
        if "network" in error_msg.lower() or "connection" in error_msg.lower():
            return "Brak połączenia z OpenAI. Sprawdź połączenie internetowe."
        
        return f"Błąd podczas generowania komentarza AI: {error_msg}"
    
    @staticmethod
    def handle_generic_error(error: Exception, context: str = "", default_message: str = "Wystąpił nieoczekiwany błąd") -> HTTPException:
        """
        Obsługuje ogólne błędy z logowaniem
        
        Args:
            error: Wyjątek
            context: Kontekst operacji
            default_message: Domyślny komunikat błędu
        
        Returns:
            HTTPException
        """
        error_msg = str(error)
        error_type = type(error).__name__
        
        # Loguj szczegóły błędu
        logger.error(
            f"Generic error in {context}: {error_type} - {error_msg}",
            extra={
                "error_type": error_type,
                "error_message": error_msg,
                "context": context,
                "full_error": str(error)
            },
            exc_info=True
        )
        
        return HTTPException(
            status_code=500,
            detail=default_message
        )

