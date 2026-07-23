"""
Chainlit chat app: an oncall assistant that answers questions using wiki
articles indexed by build_index.py, retrieved via query.py, and answered by
Anthropic Claude.

Run with:
    chainlit run app.py -w
"""

import os

import chainlit as cl
from anthropic import Anthropic
from dotenv import load_dotenv

from query import retrieve

load_dotenv()

ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5")
_anthropic_client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = (
    "You are an oncall assistant. Answer the engineer's question using ONLY "
    "the wiki excerpts provided below. If the excerpts don't contain the "
    "answer, say so plainly instead of guessing. Cite the source title for "
    "any fact you use."
)


def build_prompt(question: str, chunks: list[dict]) -> str:
    context = "\n\n".join(
        f"[{c['title']}]({c['url']})\n{c['text']}" for c in chunks
    )
    return f"Wiki excerpts:\n{context}\n\nQuestion: {question}"


@cl.on_message
async def on_message(message: cl.Message) -> None:
    chunks = retrieve(message.content)

    if not chunks:
        await cl.Message(
            content="I couldn't find anything relevant in the indexed wiki articles. "
            "Run fetch_articles.py and build_index.py first."
        ).send()
        return

    response = _anthropic_client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": build_prompt(message.content, chunks)}],
    )

    answer = "".join(block.text for block in response.content if block.type == "text")
    sources = "\n".join(f"- [{c['title']}]({c['url']})" for c in {c['url']: c for c in chunks}.values())

    await cl.Message(content=f"{answer}\n\n**Sources:**\n{sources}").send()
