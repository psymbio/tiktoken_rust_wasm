Okay, so here are some testing results:

Testing Environment: Jupyter Lite (https://jupyter.org/try-jupyter/lab/)

Test Case 1:
```python
import micropip
await micropip.install('urllib3', keep_going=True)
import urllib3

await micropip.install("ssl")
import ssl
http = urllib3.PoolManager()
url = "https://swapi.dev/api/people/1"
response = http.request('GET', url)
print("Status code:", response.status)
print("Response data:", response.data.decode('utf-8'))
```
Fails with: `MaxRetryError: HTTPSConnectionPool(host='swapi.dev', port=443): Max retries exceeded with url: /api/people/1 (Caused by NewConnectionError('<urllib3.connection.HTTPSConnection object at 0x219da68>: Failed to establish a new connection: [Errno 50] Protocol not available'))`

Test Case 2:
```python
import micropip
await micropip.install('https://raw.githubusercontent.com/psymbio/tiktoken_rust_wasm/main/packages/urllib3/urllib3-2.1.0-py3-none-any.whl', keep_going=True)
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
http = urllib3.PoolManager()
url = "https://swapi.dev/api/people/1"
response = http.request('GET', url)
assert response.status == 200
print("Response data:", response.data.decode('utf-8'))
```
This passes.

However, I think I'm still stuck on how to test this for streaming requests/responses. Also, I'm stuck on supporting the streaming responses/requests.

Currently, I'm looking at ways to support httpx based libraries on Pyodide (https://github.com/pyodide/pyodide/issues/4292) and OpenAI has implemented configuring http clients (https://github.com/openai/openai-python/blob/main/README.md#configuring-the-http-client). 