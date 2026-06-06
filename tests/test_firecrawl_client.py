from scraper.firecrawl_client import _extract_content


def test_extract_content_prefers_html_when_available() -> None:
    result = {
        "markdown": "| No. | CPC |\n| --- | --- |",
        "html": "<table><tr><td>1</td><td>481200102</td></tr></table>",
    }

    assert _extract_content(result) == result["html"]


def test_extract_content_prefers_nested_html_when_available() -> None:
    result = {
        "data": {
            "markdown": "| No. | CPC |\n| --- | --- |",
            "html": "<table><tr><td>1</td><td>481200102</td></tr></table>",
        }
    }

    assert _extract_content(result) == result["data"]["html"]
