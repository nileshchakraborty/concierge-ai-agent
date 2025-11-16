from ...adapters import search_adapter, browse_adapter, ollama_adapter, email_adapter
from fastapi import HTTPException
import json
from .gemma_agent_service import GemmaAgentService
from .ai_agent_service_impl import AiAgentServiceImpl
from ... import config


class ConciergeAgentService(GemmaAgentService):
    # Adapter manager will be injected into instances by DI provider
    def __init__(self, adapter_manager=None, http_client=None):
        self._adapter_manager = adapter_manager
        self._http_client = http_client

    async def run_concierge_agent(self, goal: str, history: list) -> str:
        # Implement the same multi-step flow as the original terminal script:
        # 1) Extract email from goal using the model
        # 2) Ask model to create a concise search query
        # 3) Run the search
        # 4) Ask model to pick promising URLs
        # 5) Browse those URLs
        # 6) Summarize findings via the model
        # 7) Ask model whether to send an email and send if appropriate

        async def _call_model(prompt: str) -> str:
            adapter_name = DEFAULT_ADAPTER
            try:
                resp = await self._adapter_manager.call_adapter(adapter_name, prompt, client=self._http_client)
            except Exception:
                try:
                    resp = await ollama_adapter.call_gemma(prompt, client=self._http_client)
                except Exception:
                    # fallback to sync call if adapter is sync — handle async coroutines too
                    import asyncio

                    tmp = ollama_adapter.call_gemma(prompt)
                    if asyncio.iscoroutine(tmp):
                        resp = await tmp
                    else:
                        resp = tmp

            # Normalise response to string
            if isinstance(resp, dict):
                text = resp.get("text") or resp.get("response") or resp.get("result")
                if isinstance(text, (dict, list)):
                    try:
                        return json.dumps(text)
                    except Exception:
                        return str(text)
                return text or str(resp)
            return str(resp)

        results = {}

        # 0. Extract recipient email from goal
        prompt_extract_email = f"""
You are an expert at finding email addresses in text.
Analyze the following user request and extract the email address if one is present.
If you find an email address, respond with ONLY the email address.
If you do not find an email address, respond with the word "none".

User request: "{goal}"
"""
        import asyncio

        recipient_email_from_goal = (await _call_model(prompt_extract_email)).strip()
        if "@" not in recipient_email_from_goal:
            recipient_email_from_goal = "none"

        # 1. Create a search query
        formatted_history = "\n".join(history) if history else ""
        prompt_query = f"""
You are a helpful concierge agent. Your task is to understand a user's request and generate a concise, effective search query to find the information they need.

Conversation history:
---
{formatted_history}
---
User's latest request: "{goal}"

Based on the request, what is the best, simple search query for Google?
The query should be 3-5 words.
Respond with ONLY the search query itself.
"""
        search_query = (await _call_model(prompt_query)).strip().replace('"', '')

        # 2. Perform search
        # Pass the injected http client if available
        try:
            search_results = await search_adapter.search_web(search_query, client=self._http_client)
        except TypeError:
            # fallback for sync adapter signature
            import asyncio

            search_results = asyncio.get_event_loop().run_until_complete(search_adapter.search_web(search_query))

        # If the adapter returned an error dict, escalate to an HTTP error so the API returns
        # a meaningful HTTP status (503 Service Unavailable) rather than a generic 200 response.
        if isinstance(search_results, dict) and search_results.get("error"):
            detail = search_results.get("text") or search_results.get("error") or "Search provider error"
            raise HTTPException(status_code=503, detail=detail)

        results["search"] = search_results

        # 3. Ask model to pick top URLs
        prompt_pick_urls = f"""
You are a smart web navigator. Your task is to analyze Google search results and select the most promising URLs to find the answer to a user's goal. Avoid generic homepages and prefer specific articles, lists, or maps.

User's goal: "{goal}"

Search Results:
---
{search_results.get('text') if isinstance(search_results, dict) else str(search_results)}
---

Based on the user's goal and the search results, which are the top 2-3 most promising and specific URLs to browse for details?
Respond with ONLY a list of URLs, one per line.
"""
        browse_urls_str = (await _call_model(prompt_pick_urls)).strip()
        browse_urls = [u.strip() for u in browse_urls_str.splitlines() if u.strip().startswith('http')]

        if not browse_urls:
            # fallback: try summarizing from snippets
            prompt_summarize_snippets = f"""
You are a helpful concierge agent. The web browser is not working, but you have search result snippets.
User's goal: "{goal}"
Search Results:
---
{search_results.get('text') if isinstance(search_results, dict) else str(search_results)}
---
Please provide a summary based *only* on the search result snippets. Do not suggest browsing URLs.
"""
            final_summary = await _call_model(prompt_summarize_snippets)
            return final_summary

        # 4. Browse the websites
        all_website_texts = []
        for url in browse_urls:
            try:
                text = await browse_adapter.browse_website(url, client=self._http_client)
            except TypeError:
                # fallback for sync adapter
                import asyncio

                text = asyncio.get_event_loop().run_until_complete(browse_adapter.browse_website(url))
            if not str(text).startswith("Error"):
                all_website_texts.append(f"Content from {url}:\n{text}")

        if not all_website_texts:
            # Escalate browsing failures to the API caller with a 503 status.
            raise HTTPException(
                status_code=503,
                detail=("Browsing failed: I tried to visit the candidate URLs but was blocked "
                        "or couldn't retrieve any usable content. Please check network/access or try again."),
            )

        aggregated_text = "\n\n---\n\n".join(all_website_texts)

        # 5. Summarize everything for the user
        prompt_summarize = f"""
You are a meticulous and trustworthy concierge agent. Your primary goal is to provide a clear, concise, and, above all, ACCURATE answer to the user's request by synthesizing information from multiple sources.

User's latest request: "{goal}"

You have gathered the following text from one or more websites:
---
{aggregated_text}
---

Fact-Check and Synthesize:
Based on the information above, provide a comprehensive summary that directly answers the user's request.
Before including any business or item in your summary, you MUST verify that it meets ALL the specific criteria from the user's request.
If you cannot find explicit confirmation that a business meets a criterion, DO NOT include it in the summary.

Format your response clearly for the user. If listing places, use bullet points.
"""
        final_summary = await _call_model(prompt_summarize)

        # 6. Decide whether to send an email and draft it
        prompt_email_decision = f"""
You are a highly capable assistant responsible for drafting clear and detailed emails based on a research summary.

User's original request: "{goal}"

Here is the final summary of the research, which has been fact-checked to meet the user's criteria:
---
{final_summary}
---

Here is a reminder of the raw text gathered from the websites, which you can use to find details like reservation links:
---
{aggregated_text}
---

Your task is to decide if an email is appropriate to send to the user with this information. If it is, you must draft the email.

- If the summary contains useful, actionable information, then an email should be sent.
- If the summary is short, conversational, or indicates no results were found, an email is not needed.

Respond in JSON format.
If sending, the JSON should be: {{"send_email": true, "subject": "...", "body": "..."}}
If not sending, the JSON should be: {{"send_email": false}}
"""
        email_decision_str = await _call_model(prompt_email_decision)
        try:
            email_decision = json.loads(email_decision_str)
            subject = email_decision.get("subject")
            body = email_decision.get("body")
            recipient = recipient_email_from_goal if recipient_email_from_goal != "none" else None

            if subject and body and recipient:
                try:
                    # email_adapter is now async; await it directly
                    email_result = await email_adapter.send_email(recipient, subject, body, self._http_client)
                    results["email"] = email_result
                except TypeError:
                    # fallback if adapter still presents sync signature
                    import asyncio
                    email_result = await asyncio.to_thread(email_adapter.send_email, recipient, subject, body)
                    results["email"] = email_result
                except Exception:
                    # ignore parse/send errors and continue
                    pass
            results["summary"] = final_summary
        except Exception:
            # Handle potential errors during JSON parsing or other operations
            pass
        return final_summary


# NOTE: Adapter registration and DEFAULT_ADAPTER are handled by the DI wiring
DEFAULT_ADAPTER = getattr(config, "DEFAULT_AI_ADAPTER", "gemma") or "gemma"

