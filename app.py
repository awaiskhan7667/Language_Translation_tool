from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import gradio as gr

app = FastAPI()

# -----------------------------
# Translation Models
# -----------------------------

class TranslationRequest(BaseModel):
    text: str
    source_lang: str
    target_lang: str

class TranslationResponse(BaseModel):
    translated_text: str

# -----------------------------
# Config
# -----------------------------

TRANSLATION_API_URL = "http://localhost:5000/translate"

SUPPORTED_LANGUAGES = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "ru": "Russian",
    "zh": "Chinese",
    "ar": "Arabic",
    "tr": "Turkish",
    "ja": "Japanese",
    "ko": "Korean",
    "hi": "Hindi"
}

# -----------------------------
# FastAPI Endpoint
# -----------------------------

@app.post("/translate", response_model=TranslationResponse)
async def translate_text(request: TranslationRequest):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text is required.")

    if request.source_lang not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=400, detail=f"Unsupported source language: {request.source_lang}")
    if request.target_lang not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=400, detail=f"Unsupported target language: {request.target_lang}")

    payload = {
        "q": request.text,
        "source": request.source_lang,
        "target": request.target_lang,
        "format": "text"
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                TRANSLATION_API_URL,
                data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            response.raise_for_status()
            data = response.json()

            if "translatedText" not in data:
                raise HTTPException(status_code=500, detail="Unexpected API response format.")

            return TranslationResponse(translated_text=data["translatedText"])
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=500, detail=f"Translation service error: {e.response.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# -----------------------------
# Gradio UI
# -----------------------------

async def translate_gradio(text, source_lang_name, target_lang_name):
    # Convert language names to codes
    inv_langs = {v: k for k, v in SUPPORTED_LANGUAGES.items()}
    source_lang = inv_langs[source_lang_name]
    target_lang = inv_langs[target_lang_name]

    request = TranslationRequest(
        text=text,
        source_lang=source_lang,
        target_lang=target_lang
    )

    response = await translate_text(request)
    return response.translated_text

# Interface
demo = gr.Interface(
    fn=translate_gradio,
    inputs=[
        gr.Textbox(label="Enter text to translate"),
        gr.Dropdown(choices=list(SUPPORTED_LANGUAGES.values()), label="Source Language", value="English"),
        gr.Dropdown(choices=list(SUPPORTED_LANGUAGES.values()), label="Target Language", value="Spanish")
    ],
    outputs=gr.Textbox(label="Translated Text"),
    title="🈺 Simple Translator",
    description="Translate text between multiple languages using a local LibreTranslate server. No API key required!"
)

# Launch Gradio (only when running as main)
if __name__ == "__main__":
    demo.launch()
