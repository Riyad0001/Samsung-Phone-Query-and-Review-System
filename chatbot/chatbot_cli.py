"""
CLI interface for the Samsung Phone Chatbot.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chatbot.rag_chatbot import SamsungChatbot


def run_cli():
    print("=" * 60)
    print("   SAMSUNG PHONE QUERY & REVIEW SYSTEM")
    print("   Type 'exit' to quit, 'help' for sample queries")
    print("=" * 60)

    chatbot = SamsungChatbot(llm_pipeline=None, embedder=None)
    try:
        from sentence_transformers import SentenceTransformer
        print("[INFO] Loading embedding model (all-MiniLM-L6-v2)...")
        embedder = SentenceTransformer("all-MiniLM-L6-v2")
        chatbot.engine.embedder = embedder
    except Exception as e:
        print(f"[INFO] Embedding model not available ({e}), using keyword search only.")

    chatbot.engine.build_index()

    while True:
        try:
            user_input = input("\n🤔 You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit"):
            print("Goodbye!")
            break
        if user_input.lower() == "help":
            print("\nSample queries:")
            print('  "What are the camera specs of the Samsung Galaxy S23?"')
            print('  "Which Samsung phone has the best battery life?"')
            print('  "Compare Galaxy S23 and S22"')
            print('  "List all phones"')
            print('  "Tell me about Galaxy S24 Ultra"')
            continue

        answer = chatbot.answer_query(user_input)
        print(f"\n🤖 Bot:\n{answer}")


if __name__ == "__main__":
    run_cli()