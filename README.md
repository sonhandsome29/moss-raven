Thai Duong Son

`kb-raven` scrapes public OptiSigns support articles, converts them to clean Markdown, chunks them, and uploads only new or changed content to an OpenAI vector store.

## Setup

1. Copy `.env.sample` to `.env`.
2. Fill in `OPENAI_API_KEY`.
3. Optionally set `OPENAI_VECTOR_STORE_ID` to reuse an existing vector store.
4. Install dependencies with `pip install -r requirements.txt`.
5. For GitHub Actions, add repo secrets `OPENAI_API_KEY` and optionally `OPENAI_VECTOR_STORE_ID`.

## Run locally

Run `python main.py`.

The job re-scrapes Zendesk, writes Markdown to `data/articles/`, writes chunk files to `data/chunks/`, stores sync state in `data/manifests/state.json`, and logs `added`, `updated`, and `skipped`.

Chunking strategy: split by Markdown headings first, then split oversized sections by paragraph with a small overlap so support steps stay grouped for retrieval.

Docker run:

```bash
docker build -t kb-raven .
docker run --rm --env-file .env -v ${PWD}/data:/app/data kb-raven
```

## Daily job logs

Platform: GitHub Actions scheduled workflow (`.github/workflows/daily-sync.yml`)  
Workflow link: `https://github.com/<your-user>/<your-repo>/actions/workflows/daily-sync.yml`

The workflow runs once per day, uploads `sync.log` as an artifact, and commits the updated `state.json` so delta detection persists across runs.

## Assistant screenshot

Sample question: `How do I add a YouTube video?`

Screenshot(s): ![Assistant answer](test1.png)
![Assistant answer](test2.png)
![Assistant answer](test3.png)
