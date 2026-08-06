import logging
import os

logger = logging.getLogger(__name__)


class SiebelGenerator:
    def __init__(self):
        self.use_ollama = os.environ.get("USE_OLLAMA", "true").lower() == "true"
        self.ollama_model = os.environ.get("OLLAMA_MODEL", "llama3.2")
        self.openai_model = os.environ.get("OPENAI_CHAT_MODEL", "gpt-4o-mini")
        self.openai_api_key = os.environ.get("OPENAI_API_KEY", "")

    def _build_prompt(self, query: str, context_docs: list) -> str:
        context_text = ""
        for i, doc in enumerate(context_docs):
            text = doc.get("text", "")[:500]
            source = doc.get("metadata", {}).get("source", "Unknown")
            section = doc.get("metadata", {}).get("section_title", "")
            similarity = doc.get("relevance_score", doc.get("similarity", 0))

            context_text += (
                f"\n--- Document {i+1} (Source: {source}, Section: {section}, "
                f"Relevance: {similarity:.2f}) ---\n"
                f"{text}\n"
            )

        prompt = (
            f"You are an expert on Oracle Siebel CRM (version 6 and later). "
            f"Answer the user's question based ONLY on the provided context documents. "
            f"If the answer cannot be found in the context, say so explicitly.\n\n"
            f"Context Documents:{context_text}\n\n"
            f"Question: {query}\n\n"
            f"Answer:"
        )

        return prompt

    def generate(self, query: str, context_docs: list) -> str:
        if not context_docs:
            return (
                f"No relevant documents found for query: '{query}'. "
                f"Try rephrasing your question or ensure the knowledge base has been populated."
            )

        prompt = self._build_prompt(query, context_docs)

        if self.use_ollama:
            result = self._generate_ollama(prompt)
            if result is not None:
                return result

        if self.openai_api_key:
            result = self._generate_openai(prompt)
            if result is not None:
                return result

        return self._generate_fallback(query, context_docs)

    def _generate_ollama(self, prompt: str):
        try:
            import ollama
            response = ollama.generate(
                model=self.ollama_model,
                prompt=prompt,
                options={"temperature": 0.3, "top_p": 0.9},
            )
            return response.get("response", "No response generated.")
        except ImportError:
            logger.warning("ollama package not installed, using fallback")
            return None
        except Exception as e:
            logger.error("Ollama generation failed: %s", e)
            return None

    def _generate_openai(self, prompt: str):
        try:
            from langchain_openai import ChatOpenAI
            from langchain.schema import HumanMessage, SystemMessage

            llm = ChatOpenAI(
                model=self.openai_model,
                api_key=self.openai_api_key,
                temperature=0.3,
            )

            messages = [
                SystemMessage(content=(
                    "You are an expert on Oracle Siebel CRM. "
                    "Answer based ONLY on the provided context."
                )),
                HumanMessage(content=prompt),
            ]
            response = llm.invoke(messages)
            return response.content
        except Exception as e:
            logger.error("OpenAI generation failed: %s", e)
            return None

    def _generate_fallback(self, query: str, context_docs: list) -> str:
        combined = " ".join(
            d.get("text", "")[:300] for d in context_docs[:3]
        )
        return (
            f"Based on the retrieved documents, here is what I found:\n\n"
            f"Query: {query}\n\n"
            f"Relevant context (excerpt):\n{combined[:1500]}\n\n"
            f"Note: No LLM backend configured. Set USE_OLLAMA=false and provide "
            f"OPENAI_API_KEY for full generation, or install ollama for local generation."
        )