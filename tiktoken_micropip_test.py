import micropip
micropip.install('https://github.com/psymbio/tiktoken_wasm/blob/main/dist/tiktoken-0.0.0-py3-none-any.whl')
import tiktoken.registry as registry
from tiktoken.registry import _find_constructors
from tiktoken.core import Encoding

_find_constructors()

print("defining constructor")
constructor = registry.ENCODING_CONSTRUCTORS['cl100k_base']
params = constructor()

print("initializing the Encoding class")
enc = Encoding(**params)

print("encoding...")
string = "hello world"
encoded_string = enc.encode(string)
print(string, " was encoded to: ", encoded_string)