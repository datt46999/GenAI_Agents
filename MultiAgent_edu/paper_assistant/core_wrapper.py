import os
import urllib3
import time


from pydantic import BaseModel, Field
from typing import ClassVar

class CoreAPIWrapper(BaseModel):
    base_url : ClassVar[str] = ""
    api_key : ClassVar[str] = os.environ("CORE_API_KEY")

    top_results = Field(decription = "Top results obtained by running query on Core", default = 1)

    def _get_generate_response(self, query: str)-> dict:
        http = urllib3.PoolManager()

        max_retries = 5

        for attempt in range(max_retries):
            response = http.request(
                'GET',
                f"{self.base_url}/search/outputs", 
                headers={"Authorization": f"Bearer {self.api_key}"}, 
                fields={"q": query, "limit": self.top_k_results}
            )
            if 200 <= response.status < 300:
                return response.json()
            elif attempt < max_retries - 1:
                time.sleep(2 ** (attempt + 2))
            else:
                raise Exception(f"Got non 2xx response from CORE API: {response.status} {response.data}")

    def search(self, query: str)-> str:
        responses = self._get_generate_response(query)
        results = responses.get('results', [])

        if not results:
            return "No Relevant result can found!!!"

        # format of result in string
        docs =[]
        for result in results:
            published_date_str = result.get('publishedDate') or result.get('yearPublished', '')
            authors_str = ' and '.join([item['name'] for item in result.get('authors', [])])
            docs.append((
                f"* ID: {result.get('id', '')},\n"
                f"* Title: {result.get('title', '')},\n"
                f"* Published Date: {published_date_str},\n"
                f"* Authors: {authors_str},\n"
                f"* Abstract: {result.get('abstract', '')},\n"
                f"* Paper URLs: {result.get('sourceFulltextUrls') or result.get('downloadUrl', '')}"
            ))
        return "\n-----\n".join(docs)
