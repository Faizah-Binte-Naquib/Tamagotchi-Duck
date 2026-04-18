# LLM Setup Guide

This guide explains how to set up Ollama for the personality and chat features.

## Ollama Setup (Required)

The application uses Ollama as the LLM backend. Ollama handles model downloads and management automatically.

### Steps:

1. **Install Ollama**
   - Download from: https://ollama.ai
   - Install and run Ollama (it starts automatically)

2. **Download the model**
   ```powershell
   ollama pull llama3.1:8b
   ```

3. **Verify it's working**
   ```powershell
   ollama list
   ```
   You should see `llama3.1:8b` in the list.

4. **Restart the application**
   The app will automatically detect and use Ollama.

---

## Troubleshooting

### "Ollama LLM backend not available"

- **Ollama not running**: Make sure Ollama is installed and running. Check with `ollama list`
- **Model not downloaded**: Run `ollama pull llama3.1:8b` to download the model
- **Connection refused**: Ensure Ollama is running on port 11434

### Ollama connection refused

- Make sure Ollama is installed and running
- Try restarting Ollama: Close and reopen the Ollama application
- Check if port 11434 is available

---

## Model Information

The application uses `llama3.1:8b` by default. You can change this in `config/llm_config.py` if you want to use a different model.

**Available models** (via Ollama):
- `llama3.1:8b` - Default, good balance of quality and speed
- `llama3.1:70b` - Higher quality, requires more RAM
- `llama3:8b` - Alternative 8B model
- `mistral:7b` - Alternative model option

To use a different model, update `OLLAMA_MODEL` in `config/llm_config.py` and pull the model with `ollama pull <model-name>`.
