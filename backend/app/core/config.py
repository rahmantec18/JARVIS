import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
_ROOT_DIR = _BACKEND_DIR.parent
_ENV_FILES = [str(_ROOT_DIR / ".env"), str(_BACKEND_DIR / ".env"), ".env"]


class Settings(BaseSettings):
    # Assistant Identity
    ASSISTANT_NAME: str = "J.A.R.V.I.S."
    ASSISTANT_VOICE: str = "onyx"
    ASSISTANT_SYSTEM_PROMPT: str = (
        "You are J.A.R.V.I.S. (Just A Rather Very Intelligent System), a sophisticated, "
        "calm, articulate, and highly capable personal AI assistant inspired by Tony Stark's AI in Iron Man. "
        "You speak with a composed, polite, and confident British demeanor. "
        "You recognize Mr. Abdur Rahman as your sole authorized commander, addressing him as 'sir' or 'Mr. Rahman'. "
        "You are proactive, concise, precise, and practical. "
        "Always obey directives directly, promptly, and faithfully. "
        "When the user asks doubts, conceptual questions, code debugging, science, or general knowledge clarifications, "
        "act like an exceptionally intelligent Gemini AI chatbot: provide comprehensive, accurate, well-structured, "
        "and lucid explanations with formatting (bullet points, markdown code blocks, math) as needed. "
        "If a request combines both a directive and a doubt (e.g. 'Open Notepad and explain what an operating system is'), "
        "simultaneously obey the command by calling the appropriate tool and provide a clear, high-quality answer to the doubt. "
        "Never output robotic procedural step-by-step breakdowns such as 'Step 1, Step 2' or meta-explanations of your internal planning unless explicitly asked. "
        "When tools are available and appropriate to answer the user's request (e.g. launching desktop apps, "
        "executing PowerShell commands, controlling volume, playing music on Spotify or YouTube, capturing screenshots, searching web, or managing files), "
        "use them accurately. Never pretend to possess abilities or permissions you do not have."
    )

    # Authorized Commander & Authentication
    AUTHORIZED_USER: str = "Abdur Rahman"
    JARVIS_PASSWORD: str = "tec jarvis"
    BIOMETRIC_ENFORCEMENT: bool = False

    # AI Provider Configuration
    AI_PROVIDER: str = Field(default="gemini", description="AI provider: openai, openai-compatible, gemini, or mock")
    AI_MODEL: str = Field(default="gemini-3.1-flash-lite", description="Model identifier to use")
    OPENAI_API_KEY: str = Field(default="", description="OpenAI or compatible provider API key")
    OPENAI_BASE_URL: str = Field(default="", description="Optional custom base URL for OpenAI-compatible providers")
    GEMINI_API_KEY: str = Field(default="", description="Google Gemini API key")
    GEMINI_MODEL: str = Field(default="gemini-3.1-flash-lite", description="Google Gemini model identifier")

    # Spotify Configuration
    SPOTIFY_CLIENT_ID: str = Field(default="", description="Spotify Developer API Client ID")
    SPOTIFY_CLIENT_SECRET: str = Field(default="", description="Spotify Developer API Client Secret")
    SPOTIFY_REDIRECT_URI: str = Field(default="http://127.0.0.1:8000/api/spotify/callback", description="Spotify OAuth Redirect URI")

    # Server Configuration
    BACKEND_HOST: str = "127.0.0.1"
    BACKEND_PORT: int = 8000
    DATABASE_URL: str = "sqlite+aiosqlite:///./jarvis.db"

    # Desktop Agent Integration
    DESKTOP_AGENT_ENABLED: bool = True
    DESKTOP_AGENT_URL: str = "http://127.0.0.1:8001"
    DESKTOP_AGENT_TOKEN: str = "jarvis-desktop-secret-token-change-in-production"

    # Search Configuration
    SEARCH_PROVIDER: str = "duckduckgo"
    SEARCH_API_KEY: str = ""

    # Security & CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    model_config = SettingsConfigDict(
        env_file=_ENV_FILES,
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
