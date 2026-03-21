# skills/wiki_skill.py

import wikipedia #type:ignore


def wikipedia_summary(query: str, sentences: int = 2) -> str:
    """
    Return a short Wikipedia summary for the given query.
    """
    query = query.strip()
    if not query:
        return "Please tell me what you want to search on Wikipedia."

    try:
        wikipedia.set_lang("en")
        summary = wikipedia.summary(query, sentences=sentences)
        return summary
    except wikipedia.DisambiguationError as e:
        # Too many possible pages
        options = ", ".join(e.options[:5])
        return f"There are multiple results for {query}: {options}."
    except wikipedia.PageError:
        return f"I could not find a Wikipedia page for {query}."
    except Exception as e:
        return f"Something went wrong while fetching Wikipedia: {e}"
