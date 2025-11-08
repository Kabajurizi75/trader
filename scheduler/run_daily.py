from rag_engine.ingest.rss_ingest import fetch_rss_feeds
from rag_engine.vector_store.embedder import embed_texts
from rag_engine.llm.query_llm import query_llm

feeds = ["https://www.coindesk.com/arc/outboundfeeds/rss/" ]
articles = fetch_rss_feeds(feeds)
texts = [article['summary'] for article in articles]
embeddings = embed_texts(texts)
response = query_llm("Summarize today's crypto news")
print(response)
