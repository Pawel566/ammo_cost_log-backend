from typing import Optional
from openai import OpenAI
from models import Gun
from settings import settings
from services.error_handler import ErrorHandler
import logging

logger = logging.getLogger(__name__)


class AIService:
    """
    Serwis do generowania komentarzy AI na podstawie wyników strzeleckich.
    Uwzględnia poziom zaawansowania użytkownika (skill_level) do dostosowania tonu komentarza.
    """
    
    @staticmethod
    def _get_skill_level_tone(skill_level: str, accuracy: float) -> str:
        """
        Zwraca instrukcję dotyczącą tonu komentarza na podstawie poziomu zaawansowania i wyników.
        
        Args:
            skill_level: Poziom zaawansowania użytkownika ('beginner', 'intermediate', 'advanced', 'expert')
            accuracy: Procent celności (0-100)
        
        Returns:
            Instrukcja dla AI dotycząca tonu komentarza
        """
        skill_level = skill_level.lower() if skill_level else 'beginner'
        is_good_result = accuracy >= 70
        is_poor_result = accuracy < 50
        
        if skill_level in ['beginner', 'początkujący']:
            if is_poor_result:
                return "Bądź bardzo łagodny, wspierający i motywujący. Używaj pozytywnego języka, podkreślaj postęp i zachęcaj do dalszej praktyki."
            elif is_good_result:
                return "Bądź entuzjastyczny i gratuluj dobrych wyników. Podkreślaj postęp i zachęcaj do kontynuacji."
            else:
                return "Bądź wspierający i konstruktywny. Wskaż obszary do poprawy w delikatny sposób."
        
        elif skill_level in ['intermediate', 'średniozaawansowany']:
            if is_poor_result:
                return "Bądź konstruktywny i pomocny. Wskaż konkretne obszary do poprawy, ale w sposób wspierający."
            elif is_good_result:
                return "Bądź profesjonalny i doceniaj wyniki. Wskaż mocne strony i sugestie dalszego rozwoju."
            else:
                return "Bądź zbalansowany - doceniaj postęp i wskazuj obszary do poprawy."
        
        elif skill_level in ['advanced', 'zaawansowany', 'expert', 'ekspert']:
            if is_poor_result:
                return "Możesz być bardziej bezpośredni i szczery. Możesz delikatnie żartować lub lekko szydzić, ale w sposób konstruktywny. Użyj humoru, ale nie bądź złośliwy."
            elif is_good_result:
                return "Bądź profesjonalny i precyzyjny w analizie. Wskaż nawet drobne szczegóły do poprawy, ponieważ użytkownik jest zaawansowany."
            else:
                return "Bądź bezpośredni i konstruktywny. Wskaż konkretne błędy i sposoby ich poprawy."
        
        # Domyślnie dla nieznanego poziomu
        return "Bądź profesjonalny i konstruktywny."
    
    @staticmethod
    async def generate_comment(
        gun: Gun,
        distance_m: float,
        hits: int,
        shots: int,
        accuracy: float,
        skill_level: str = "beginner",
        api_key: Optional[str] = None
    ) -> str:
        """
        Generuje komentarz AI na podstawie wyników strzeleckich.
        
        Args:
            gun: Obiekt broni
            distance_m: Dystans w metrach
            hits: Liczba trafień
            shots: Liczba strzałów
            accuracy: Procent celności (0-100)
            skill_level: Poziom zaawansowania użytkownika
            api_key: Klucz API OpenAI (opcjonalny, jeśli None używa z settings)
        
        Returns:
            Wygenerowany komentarz AI
        """
        if not api_key:
            api_key = settings.openai_api_key
        
        if not api_key:
            return "Brak klucza API OpenAI. Skonfiguruj OPENAI_API_KEY w zmiennych środowiskowych."
        
        try:
            client = OpenAI(api_key=api_key)
            
            # Określ ton komentarza na podstawie poziomu zaawansowania
            tone_instruction = AIService._get_skill_level_tone(skill_level, accuracy)
            
            # Przygotuj informacje o broni
            gun_info = f"{gun.name}"
            if gun.caliber:
                gun_info += f" kaliber {gun.caliber}"
            if gun.type:
                gun_info += f" ({gun.type})"
            
            # Przygotuj prompt
            prompt = f"""Jesteś ekspertem strzeleckim analizującym wyniki sesji strzeleckiej.

Dane sesji:
- Broń: {gun_info}
- Dystans: {distance_m} metrów
- Wyniki: {hits} trafień z {shots} strzałów
- Celność: {accuracy:.1f}%

{tone_instruction}

Wygeneruj krótki, konkretny komentarz (maksymalnie 100 słów) analizujący te wyniki. 
Komentarz powinien być w języku polskim i uwzględniać:
1. Ogólną ocenę wyników
2. Konkretne obserwacje dotyczące celności
3. Konstruktywne sugestie poprawy (jeśli potrzebne)
4. Pozytywne wzmocnienie (jeśli wyniki są dobre)

Bądź konkretny i użyj terminologii strzeleckiej odpowiedniej do poziomu zaawansowania użytkownika."""

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Jesteś ekspertem strzeleckim z wieloletnim doświadczeniem. Analizujesz wyniki strzeleckie i udzielasz konstruktywnych porad."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.7
            )
            
            comment = response.choices[0].message.content.strip()
            return comment
            
        except Exception as e:
            error_msg = ErrorHandler.handle_openai_error(e, "generowanie komentarza AI")
            logger.error(f"Błąd podczas generowania komentarza AI: {e}", exc_info=True)
            return f"Błąd podczas generowania komentarza: {error_msg}"



