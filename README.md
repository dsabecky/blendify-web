# Blendify Web

[![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=fff)](#)
[![Django](https://img.shields.io/badge/Django-%23092E20.svg?logo=django&logoColor=white)](#)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-7952B3?logo=bootstrap&logoColor=fff)](#)
[![Spotify](https://img.shields.io/badge/Spotify-1ED760?logo=spotify&logoColor=white)](#)
[![ChatGPT](https://img.shields.io/badge/ChatGPT-74aa9c?logo=openai&logoColor=white)](#)
[![MIT License](https://img.shields.io/badge/license-MIT-green.svg)](#LICENSE)

**Blendify Web** is a Django web app that lets users blend multiple music themes into a single Spotify playlist using OpenAI and the Spotify API. Users can log in with Spotify, select a playlist to modify, enter themes, and generate a new playlist with a custom name and description.

---

## Features

- **Spotify OAuth login**
- **Dynamic theme input** (add/remove as many as you want)
- **Option to auto-rename the playlist using AI**
- **OpenAI-powered playlist generation**
- **No duplicate songs in the final playlist**
- **Admin panel for managing playlists and songs**

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/blendify-web.git
cd blendify-web
```

### 2. Set up environment variables

Copy the example file and fill in your secrets:

```bash
cp .env.example .env
```

Edit `.env` and set your keys:

```
DJANGO_SECRET_KEY=your-django-secret-key
SPOTIFY_CLIENT_ID=your-spotify-client-id
SPOTIFY_CLIENT_SECRET=your-spotify-client-secret
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_TEMPERATURE=0.7
PLAYLIST_LENGTH=20
DJANGO_DEBUG=True
```

### 3. Run migrations

```bash
uv run manage.py migrate
```

### 4. Build static files
```bash
uv run manage.py collectstatic
```

### 5. Run the server

```bash
uv run daphne blendify.asgi:application
```
---

## Usage

1. **Log in with Spotify** (OAuth)
2. **Select a playlist** you own or can modify
3. **Enter two or more themes** (add more with the plus button)
4. **(Optional) Toggle "Playlist Rename"** to let AI name your playlist
5. **Submit** to blend your themes into a new playlist!

---

## Customization

- **Change playlist length:** Set `PLAYLIST_LENGTH` in `.env`
- **Change OpenAI model/temperature:** Set `OPENAI_MODEL` and `OPENAI_TEMPERATURE` in `.env`