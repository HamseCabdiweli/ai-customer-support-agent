# AI Customer Support Agent

A small Python 3.12 terminal chat that uses OpenAI function calling to look up orders in `orders.json`. The AI decides when to call `get_order`, then uses the result to answer. Greetings do not need an order lookup.

## Run

```sh
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Put your OpenAI API key in `.env`, then run `python app.py`. Never commit `.env`. You can change `OPENAI_MODEL` to another model that supports the Responses API and function calling.

Try `Hi`, `Where is order 1042?`, and `What about order 9999?`. Order 1042 is shipped with estimated delivery Friday. Order 9999 should get a friendly not-found reply. Type `quit` to stop.

## Tests

```sh
python -m unittest -v
```

Tests check the local data and tool-calling flow with mocked API replies, without using a key or making paid requests. Live chat needs a valid API key and internet access.
