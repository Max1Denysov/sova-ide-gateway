import html

from bs4 import BeautifulSoup


def transform_template_text(text):
    text = text.replace("<br>", "\n")
    soup = BeautifulSoup(text, "html.parser")

    for div in soup.find_all("div"):
        div.replace_with(div.text + "\n")

    out_text = soup.text.strip()
    out_text2 = html.unescape(out_text)
    return out_text2
