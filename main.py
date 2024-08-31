from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from translate import Translator

app = FastAPI()

class TranslationRequest(BaseModel):
    text: str
    in_lang: str
    out_lang: str

@app.post("/translate/")
async def translate_text(request: TranslationRequest):
    try:
        # Создаем объект переводчика
        translator = Translator(from_lang=request.in_lang, to_lang=request.out_lang)
        # Выполняем перевод
        translated_text = translator.translate(request.text)
        return {"translated_text": translated_text}
    except ValueError as e:
        # Если язык неверен
        raise HTTPException(status_code=400, detail=f"Invalid language code: {str(e)}")
    except Exception as e:
        # Для прочих исключений
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
