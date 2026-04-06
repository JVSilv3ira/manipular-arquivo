import sys
import threading
import time
from itertools import cycle

from openai import OpenAI


# Cole sua chave aqui. Exemplo: "sk-..."
API_KEY = ""

# Você pode trocar o modelo se quiser.
MODEL = "gpt-4o-mini"

# Velocidade da animação de resposta.
WORD_DELAY = 0.045
SPINNER_INTERVAL = 0.1


SYSTEM_PROMPT = (
    "You are a helpful assistant chatting with a user in a terminal. "
    "Reply naturally, clearly, and without heavy markdown."
)


def build_client() -> OpenAI:
    if not API_KEY or API_KEY == "sk-...":
        print("Preencha a variável API_KEY no início do arquivo python.py.")
        sys.exit(1)
    return OpenAI(api_key=API_KEY)


def animate_text(text: str) -> None:
    words = text.split()
    if not words:
        print()
        return

    for index, word in enumerate(words):
        end = " " if index < len(words) - 1 else ""
        print(word, end=end, flush=True)
        time.sleep(WORD_DELAY)
    print()


def spinner(stop_event: threading.Event) -> None:
    started_at = time.time()
    current_label = "Thinking"

    for frame in cycle("|/-\\"):
        if stop_event.is_set():
            break

        elapsed = time.time() - started_at
        if elapsed >= 4:
            current_label = "Searching"
        elif elapsed >= 1.5:
            current_label = "Thinking harder"

        print(f"\r{current_label} {frame}", end="", flush=True)
        time.sleep(SPINNER_INTERVAL)

    print("\r" + " " * (len(current_label) + 4) + "\r", end="", flush=True)


def print_banner() -> None:
    print("=" * 60)
    print("Chatbot de Terminal")
    print(f"Modelo atual: {MODEL}")
    print("Comandos: /sair, /limpar")
    print("=" * 60)


def fetch_response(client: OpenAI, history: list[dict[str, str]]) -> str:
    response = client.responses.create(
        model=MODEL,
        input=history,
    )
    return response.output_text.strip()


def main() -> None:
    client = build_client()
    history: list[dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]

    print_banner()

    while True:
        try:
            user_message = input("\nVocê > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nEncerrando.")
            break

        if not user_message:
            continue

        if user_message.lower() == "/sair":
            print("Encerrando.")
            break

        if user_message.lower() == "/limpar":
            history = [{"role": "system", "content": SYSTEM_PROMPT}]
            print("Histórico apagado.")
            continue

        history.append({"role": "user", "content": user_message})

        stop_event = threading.Event()
        loading_thread = threading.Thread(target=spinner, args=(stop_event,), daemon=True)
        loading_thread.start()

        try:
            answer = fetch_response(client, history)
        except Exception as exc:
            stop_event.set()
            loading_thread.join()
            history.pop()
            print(f"Erro ao chamar a API: {exc}")
            continue

        stop_event.set()
        loading_thread.join()

        history.append({"role": "assistant", "content": answer})
        print("AI   > ", end="", flush=True)
        animate_text(answer)


if __name__ == "__main__":
    main()
