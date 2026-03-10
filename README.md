# Qwen Voice Agent

This project involves building a voice agent that is powered locally by a Qwen 3.5 3B model that can perform browser tasks, as well as answer queries. 
So far, the LLM can do the following:

- Search Google for queries
- Open YouTube and search for queries / play videos
- Answer user related questions

## Dependencies
- Python
- Qwen 3.5 3B model on CPU (downloaded from Ollama)
- Playwright library for browser control

The goal of this repo is for me to play around with automation while locally running an LLM.

## Architecture

The user speaks into the microphone, which then uses the Vosk STT library to translate speech into text for the LLM. Qwen then generates the answer, which then
feeds into OpenAI's whisper module for TTS. 

