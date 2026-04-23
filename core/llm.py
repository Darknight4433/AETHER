import ollama
from loguru import logger
import core.memory as memory
from ui.state import state

class Brain:
    def __init__(self, host="http://localhost:11434", model="llama3", system_prompt=None):
        self.client = ollama.Client(host=host)
        self.host = host
        self.model = model
        self.system_prompt = system_prompt or "You are a helpful assistant."
        self.conversation_history = []
        self.available = False
        self.reset_memory()
        
        try:
            self.client.list()
            self.available = True
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
        logger.info("Thinking...")
        try:
            if not self.available:
                try:
                    self.client.list()
                    self.available = True
                except Exception as e:
                    state["error"] = f"LLM unavailable: {e}"
                    logger.error(f"Ollama unavailable: {e}")
                    return "I cannot reach the local model right now."

            recent_memory = memory.get_context()
            context_addon = ""
            try:
                from core.context_engine import get_context_prompt_addon
                context_addon = get_context_prompt_addon()
            except Exception:
                pass

            system_message = (
                f"{self.system_prompt}\n"
                "You are a real-time voice assistant."
                f"{context_addon}\n"
                "Keep responses extremely short, natural, and conversational."
            )

            messages = [{"role": "system", "content": system_message}]
            if recent_memory:
                messages.append(
                    {
                        "role": "system",
                        "content": f"Recent memory:\n{recent_memory}",
                    }
                )

            messages.extend(self.conversation_history[-6:])
            messages.append({"role": "user", "content": user_text})

            response = self.client.chat(
                model=self.model,
                messages=messages,
                options={"temperature": 0.4, "num_predict": 120},
            )
            
            reply_text = response['message']['content'].strip()
            if len(reply_text) >= 2 and reply_text[0] == reply_text[-1] and reply_text[0] in {'"', "'"}:
                reply_text = reply_text[1:-1].strip()
            if not reply_text:
                raise RuntimeError("Ollama returned an empty response.")
            
            memory.save(user_text, reply_text)
            self.conversation_history.extend(
                [
                    {"role": "user", "content": user_text},
                    {"role": "assistant", "content": reply_text},
                ]
            )
            state["error"] = ""
            
            state["status"] = "idle"
            logger.success(f"Aether: {reply_text}")
            return reply_text
            
        except Exception as e:
            self.available = False
            state["status"] = "idle"
            state["error"] = f"Ollama error: {e}"
            logger.error(f"Ollama error: {e}")
            return "I'm sorry, I'm having trouble thinking right now."
