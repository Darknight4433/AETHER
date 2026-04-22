import ollama
from loguru import logger
import core.memory as memory
from ui.state import state

class Brain:
    def __init__(self, host="http://localhost:11434", model="llama3", system_prompt=None):
        self.client = ollama.Client(host=host)
        self.model = model
        self.system_prompt = system_prompt or "You are a helpful assistant."
        self.conversation_history = []
        
        # Pull model if it doesn't exist (this might take time on first run)
        try:
            # Simple ping to check if alive
            self.client.list()
            logger.info(f"Connected to Ollama on {host}. Using model: {model}")
        except Exception as e:
            logger.error(f"Failed to connect to Ollama: {e}")
            logger.error("Make sure Ollama is running.")

    def reset_memory(self):
        """Clears the conversation history for a new call."""
        self.conversation_history = [
            {"role": "system", "content": self.system_prompt}
        ]

    def generate_response(self, user_text):
        """Sends user text to Ollama and returns the assistant's reply."""
        state["status"] = "thinking"
        logger.info(f"Thinking...")
        try:
            recent_memory = memory.get_context()
            
            # Context-aware prompt injection
            context_addon = ""
            try:
                from core.context_engine import get_context_prompt_addon
                context_addon = get_context_prompt_addon()
            except Exception:
                pass

            full_prompt = f"""You are a real-time voice assistant.{context_addon}

Keep responses:
- Extremely Short (1-2 sentences)
- Natural
- Conversational

Recent memory: 
{recent_memory}

User said: {user_text}"""


            # Build stateless messages payload
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": full_prompt}
            ]

            response = self.client.chat(
                model=self.model,
                messages=messages
            )
            
            reply_text = response['message']['content'].strip()
            
            # Save to persistent memory
            memory.save(user_text, reply_text)
            
            state["status"] = "idle"
            logger.success(f"Aether: {reply_text}")
            return reply_text
            
        except Exception as e:
            state["status"] = "idle"
            logger.error(f"Ollama error: {e}")
            return "I'm sorry, I'm having trouble thinking right now."
