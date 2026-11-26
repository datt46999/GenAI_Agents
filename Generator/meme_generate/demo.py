import asyncio
import os
import traceback
import urllib.request

from graph import create_graph
from helper_fuction import get_meme_templates

OUTPUT_DIR = "test_memes"


def _get(obj, key, default=None):
    """Read a field from either a dict or an object (e.g. a Pydantic model)."""
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _download(url: str, path: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp, open(path, "wb") as f:
        f.write(resp.read())
    return path


async def display_meme(url: str, meme_id: str, show: bool = False):
    """
    Script replacement for IPython's display():
    download the meme image, save it to OUTPUT_DIR, optionally open it with PIL.
    Returns the saved file path, or None on failure.
    """
    if not url:
        return None
    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        ext = os.path.splitext(url.split("?")[0])[1] or ".png"
        path = os.path.join(OUTPUT_DIR, f"{meme_id}{ext}")
        await asyncio.to_thread(_download, url, path)

        if show:
            try:
                from PIL import Image
                Image.open(path).show()
            except ImportError:
                pass  # Pillow not installed: file is still saved
        return path
    except Exception as e:
        print(f"Download error for {meme_id}: {e}")
        return None


async def run_workflow(website_url: str):
    """Run the full meme-generation LangGraph workflow and print the results."""
    available_templates = await get_meme_templates()

    initial_state = {
        "messages": [],
        "website_url": website_url,
        "website_content": "",
        "company_context": {
            "tone": "",
            "target_audience": "",
            "value_proposition": "",
            "key_products": [],
            "brand_personality": "",
        },
        "meme_concepts": [],
        "selected_concepts": [],
        "selected_memes": {},
        "generated_memes": {},
        "available_templates": available_templates,
    }

    app = create_graph()

    try:
        result = await app.ainvoke(initial_state)

        if not isinstance(result, dict):
            print(f"Unexpected result type: {type(result)}")
            return result

        # ---- Company analysis ----
        company_context = result.get("company_context") or {}
        if not isinstance(company_context, dict):  # Pydantic model -> dict
            company_context = (
                company_context.model_dump()
                if hasattr(company_context, "model_dump")
                else vars(company_context)
            )

        print("\nCompany Analysis:\n")
        for key, value in company_context.items():  # FIX: .items()
            if isinstance(value, list):
                value = ", ".join(map(str, value))
            print(f"{key.replace('_', ' ').title()}: {value}")

        # ---- Generated memes ----
        generated_memes = result.get("generated_memes") or {}
        if generated_memes:
            print("\nGenerated Memes:")
            for meme_id, meme_info in generated_memes.items():
                print(f"\n{meme_id.upper()}:\n")

                template_info = _get(meme_info, "template_info", {})
                print(f"Template: {_get(template_info, 'name', 'N/A')}")
                print(f"Blank template image: {_get(template_info, 'blank_template_api_link', 'N/A')}\n")

                concept = _get(meme_info, "concept", {})
                print(f"Concept message: {_get(concept, 'message', '')}")
                print(f"Concept emotion: {_get(concept, 'emotion', '')}")
                print(f"Concept audience relevance: {_get(concept, 'audience_relevance', '')}\n")

                print("Generated captions:")
                print(_get(meme_info, "generated_text_element1", ""))
                print(_get(meme_info, "generated_text_element2", ""))

                final_url = _get(meme_info, "final_url", "")
                print(f"URL: {final_url}\n")

                saved_path = await display_meme(final_url, meme_id)
                if saved_path:
                    print(f"Saved image: {saved_path}")
                else:
                    print(f"Failed to display {meme_id}")
                print("-" * 74)
        else:
            print("\nNo memes were generated.")

        return result

    except Exception as e:
        print(f"An error occurred: {e}")
        traceback.print_exc()
        return None


async def main():
    website_url = "https://www.vietnam.vn/ca-the-gioi-cho-doi-faker-trong-tran-chung-ket-lon-nhat-nam"
    print(f"Generating memes for: {website_url}")
    result = await run_workflow(website_url)

    if result:
        print("\nWorkflow completed successfully!")
    else:
        print("\nWorkflow failed. Please check the error messages above.")


if __name__ == "__main__":
    asyncio.run(main())