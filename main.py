from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from translate import Translator
from datetime import datetime
import logging
import time
import re

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('translator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Поддерживаемые языки
SUPPORTED_LANGUAGES = {
    'af': 'Afrikaans',
    'sq': 'Albanian',
    'am': 'Amharic',
    'ar': 'Arabic',
    'hy': 'Armenian',
    'az': 'Azerbaijani',
    'eu': 'Basque',
    'be': 'Belarusian',
    'bn': 'Bengali',
    'bs': 'Bosnian',
    'bg': 'Bulgarian',
    'ca': 'Catalan',
    'ceb': 'Cebuano',
    'zh': 'Chinese',
    'co': 'Corsican',
    'hr': 'Croatian',
    'cs': 'Czech',
    'da': 'Danish',
    'nl': 'Dutch',
    'en': 'English',
    'eo': 'Esperanto',
    'et': 'Estonian',
    'fi': 'Finnish',
    'fr': 'French',
    'fy': 'Frisian',
    'gl': 'Galician',
    'ka': 'Georgian',
    'de': 'German',
    'el': 'Greek',
    'gu': 'Gujarati',
    'ht': 'Haitian Creole',
    'ha': 'Hausa',
    'haw': 'Hawaiian',
    'he': 'Hebrew',
    'hi': 'Hindi',
    'hmn': 'Hmong',
    'hu': 'Hungarian',
    'is': 'Icelandic',
    'ig': 'Igbo',
    'id': 'Indonesian',
    'ga': 'Irish',
    'it': 'Italian',
    'ja': 'Japanese',
    'jv': 'Javanese',
    'kn': 'Kannada',
    'kk': 'Kazakh',
    'km': 'Khmer',
    'ko': 'Korean',
    'ku': 'Kurdish',
    'ky': 'Kyrgyz',
    'lo': 'Lao',
    'la': 'Latin',
    'lv': 'Latvian',
    'lt': 'Lithuanian',
    'lb': 'Luxembourgish',
    'mk': 'Macedonian',
    'mg': 'Malagasy',
    'ms': 'Malay',
    'ml': 'Malayalam',
    'mt': 'Maltese',
    'mi': 'Maori',
    'mr': 'Marathi',
    'mn': 'Mongolian',
    'my': 'Myanmar',
    'ne': 'Nepali',
    'no': 'Norwegian',
    'ny': 'Nyanja',
    'or': 'Odia',
    'ps': 'Pashto',
    'fa': 'Persian',
    'pl': 'Polish',
    'pt': 'Portuguese',
    'pa': 'Punjabi',
    'ro': 'Romanian',
    'ru': 'Russian',
    'sm': 'Samoan',
    'gd': 'Scots Gaelic',
    'sr': 'Serbian',
    'st': 'Sesotho',
    'sn': 'Shona',
    'sd': 'Sindhi',
    'si': 'Sinhala',
    'sk': 'Slovak',
    'sl': 'Slovenian',
    'so': 'Somali',
    'es': 'Spanish',
    'su': 'Sundanese',
    'sw': 'Swahili',
    'sv': 'Swedish',
    'tl': 'Tagalog',
    'tg': 'Tajik',
    'ta': 'Tamil',
    'tt': 'Tatar',
    'te': 'Telugu',
    'th': 'Thai',
    'tr': 'Turkish',
    'tk': 'Turkmen',
    'uk': 'Ukrainian',
    'ur': 'Urdu',
    'ug': 'Uyghur',
    'uz': 'Uzbek',
    'vi': 'Vietnamese',
    'cy': 'Welsh',
    'xh': 'Xhosa',
    'yi': 'Yiddish',
    'yo': 'Yoruba',
    'zu': 'Zulu'
}

class TranslatorHandler(BaseHTTPRequestHandler):
    def _send_response(self, status_code, data):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def _send_error(self, status_code, message):
        self._send_response(status_code, {
            "error": message,
            "status_code": status_code,
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        })

    def do_OPTIONS(self):
        self._send_response(200, {"status": "ok"})

    def detect_language(self, text):
        """Простое определение языка по скрипту"""
        scripts = {
            'Cyrillic': (r'[\u0400-\u04FF]', 'ru'),
            'Latin': (r'[a-zA-Z]', 'en'),
            'Chinese': (r'[\u4E00-\u9FFF]', 'zh'),
            'Japanese': (r'[\u3040-\u309F\u30A0-\u30FF]', 'ja'),
            'Korean': (r'[\u3130-\u318F\uAC00-\uD7AF]', 'ko'),
            'Arabic': (r'[\u0600-\u06FF]', 'ar'),
            'Devanagari': (r'[\u0900-\u097F]', 'hi'),
            'Kazakh': (r'[ҚқҮүҰұҢңӘәІіҒғ]', 'kk')
        }
        
        for script, (pattern, lang) in scripts.items():
            if re.search(pattern, text):
                return lang
        return 'en'

    def do_GET(self):
        if self.path == '/languages':
            self._send_response(200, {"languages": SUPPORTED_LANGUAGES})
        elif self.path == '/health':
            self._send_response(200, {
                "status": "healthy",
                "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                "version": "2.0.0"
            })
        else:
            self._send_error(404, "Not found")

    def do_POST(self):
        if self.path == '/translate':
            try:
                # Получение данных из запроса
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))

                # Валидация входных данных
                if not all(k in data for k in ['text', 'source_lang', 'target_lang']):
                    self._send_error(400, "Missing required fields: text, source_lang, target_lang")
                    return

                text = data['text'].strip()
                source_lang = data['source_lang']
                target_lang = data['target_lang']

                # Проверка текста
                if not text:
                    self._send_error(400, "Text cannot be empty")
                    return

                if len(text) > 5000:
                    self._send_error(400, "Text length must not exceed 5000 characters")
                    return

                # Автоопределение языка, если указан 'auto'
                if source_lang == 'auto':
                    source_lang = self.detect_language(text)

                # Проверка поддерживаемых языков
                if source_lang not in SUPPORTED_LANGUAGES:
                    self._send_error(400, f"Source language '{source_lang}' is not supported")
                    return

                if target_lang not in SUPPORTED_LANGUAGES:
                    self._send_error(400, f"Target language '{target_lang}' is not supported")
                    return

                start_time = time.time()

                try:
                    # Создание переводчика и выполнение перевода
                    translator = Translator(
                        from_lang=source_lang,
                        to_lang=target_lang,
                        email='your-email@example.com'  # Рекомендуется указать ваш email
                    )
                    translated_text = translator.translate(text)

                    if not translated_text:
                        raise ValueError("Empty translation result")

                    translation_time = time.time() - start_time

                    # Логирование успешного перевода
                    logger.info(
                        f"Translation completed: {source_lang} -> {target_lang}, "
                        f"chars: {len(text)}, time: {translation_time:.2f}s"
                    )

                    self._send_response(200, {
                        "translated_text": translated_text,
                        "source_lang": source_lang,
                        "target_lang": target_lang,
                        "detected_lang": source_lang if data['source_lang'] == 'auto' else None,
                        "translation_time": round(translation_time, 3),
                        "chars": len(text),
                        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                    })

                except Exception as e:
                    logger.error(f"Translation error: {str(e)}", exc_info=True)
                    self._send_error(500, f"Translation service error: {str(e)}")

            except json.JSONDecodeError:
                self._send_error(400, "Invalid JSON in request body")
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}", exc_info=True)
                self._send_error(500, f"Internal server error: {str(e)}")
        else:
            self._send_error(404, "Not found")

def run_server(port=8000):
    server_address = ('', port)
    httpd = HTTPServer(server_address, TranslatorHandler)
    print(f"Starting server on port {port}...")
    logger.info(f"Server started on port {port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        logger.info("Server shutdown")
        httpd.server_close()

if __name__ == '__main__':
    run_server()