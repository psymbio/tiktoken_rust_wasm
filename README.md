# Emscripten Setup for Python+Rust (non-pure Python) Packages

The following steps are for the Linux environment.

## Creating a pyodide docker container
Now we need to create a pyodide package for tiktoken refer to https://github.com/pyodide/pyodide/blob/main/docs/development/new-packages.md and https://github.com/huggingface/tokenizers/issues/1010
```bash
git clone https://github.com/pyodide/pyodide && cd pyodide
# pre-built flag is not present as stated in issue 1010 of huggingface tokenizer
./run_docker
make

# installing rust with nightly toolchain
sudo apt update
sudo apt install curl -y

curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source $HOME/.cargo/env
rustup toolchain install nightly
rustup target add --toolchain nightly wasm32-unknown-emscripten
rustup component add rust-src --toolchain nightly-x86_64-unknown-linux-gnu

# once this is done we need to install maturin and  emsdk
pip install -U maturin
pip install ./pyodide-build

# Set up emscripten 3.1.14. As of pyodide 0.21.0a3, pyodide is compiled against emscripten 3.1.14 and any extension module must also be compiled against the same version.
# https://github.com/pola-rs/polars/issues/3672
rm -rf emsdk
git clone https://github.com/emscripten-core/emsdk.git # tested and working at commit hash 961e66c
cd emsdk/
./emsdk install 3.1.45 # new update changed from 3.1.14 to 3.1.45
./emsdk activate 3.1.45
source "/src/emsdk/emsdk_env.sh"

cd ..
# https://github.com/huggingface/tokenizers/issues/1010

# NEW UPDATE: NOW CHANGING THE CLONE OF TIKTOKEN
# git clone https://github.com/openai/tiktoken.git
git clone https://github.com/psymbio/tiktoken

# UPDATE 2023/11/01: changing to the cached_weights branch
cd tiktoken
git branch
git checkout cached_weights

pip install --upgrade pip
pip install setuptools_rust pyodide-http
sudo apt-get install pkg-config libssl-dev

# python setup.py install --user
pip install .
cd ..
sudo apt-get install vim -y
vim tiktoken_test.py
```

Once the file opens paste the following into it
```python
import tiktoken
enc = tiktoken.get_encoding("cl100k_base")
if (enc.decode(enc.encode("hello world")) == "hello world"):
    print("encoding and decoding test passed!")
else:
    print("encoding and decoding test failed...")

# To get the tokeniser corresponding to a specific model in the OpenAI API:
enc = tiktoken.encoding_for_model("gpt-4")
```

Running this using `python3 tiktoken_test.py` should print the following:
```bash
encoding and decoding test passed!
```

```bash
# in the tiktoken directory - this builds the tiktoken wasm wheel
cd tiktoken/
RUSTUP_TOOLCHAIN=nightly maturin build --release -o dist --target wasm32-unknown-emscripten -i python3.10
```

Then we need to download the wheel. So, outside the docker container terminal i.e. your own terminal run the following

```bash
docker ps -a
# notedown the container id that your container runs on
# now download the wheel file to your local filesystem
# for me this looked like
docker cp 293695c6e022:/src/tiktoken/dist/tiktoken-0.5.1-cp310-cp310-emscripten_3_1_45_wasm32.whl .
```

Now after checking the compilation of the code I end up with this error:
```javascript
Uncaught (in promise) PythonError: Traceback (most recent call last):
  File "/lib/python3.11/site-packages/micropip/_commands/install.py", line 142, in install
    await transaction.gather_requirements(requirements)
  File "/lib/python3.11/site-packages/micropip/transaction.py", line 204, in gather_requirements
    await asyncio.gather(*requirement_promises)
  File "/lib/python3.11/site-packages/micropip/transaction.py", line 215, in add_requirement
    check_compatible(wheel.filename)
  File "/lib/python3.11/site-packages/micropip/_utils.py", line 183, in check_compatible
    raise ValueError(
ValueError: Wheel abi 'cp310' is not supported. Supported abis are 'abi3' and 'cp311'.

    at new_error (pyodide.asm.js:9:12519)
    at pyodide.asm.wasm:0x158827
    at pyodide.asm.wasm:0x15fcd5
    at _PyCFunctionWithKeywords_TrampolineCall (pyodide.asm.js:9:123052)
    at pyodide.asm.wasm:0x1a3091
    at pyodide.asm.wasm:0x289e4d
    at pyodide.asm.wasm:0x1e3f77
    at pyodide.asm.wasm:0x1a3579
    at pyodide.asm.wasm:0x1a383a
    at pyodide.asm.wasm:0x1a38dc
    at pyodide.asm.wasm:0x2685c5
    at pyodide.asm.wasm:0x26e3d0
    at pyodide.asm.wasm:0x1a3a04
    at pyodide.asm.wasm:0x1a3694
    at pyodide.asm.wasm:0x15f45e
    at Module.callPyObjectKwargs (pyodide.asm.js:9:81732)
    at Module.callPyObject (pyodide.asm.js:9:82066)
    at wrapper (pyodide.asm.js:9:58562)
```

Google search https://www.google.com/search?q=emscripten+cp310 lands you here https://pyodide.org/en/latest/development/building-and-testing-packages.html Therefore, I'm going back to the docker container to check if the build 


```
# in the docker container
# in src/tiktoken
pyodide build
# an error said consider running: `rustup default nightly` 
rustup default nightly
pyodide build
```

Then once again copy it to your local from the docker container (tiktoken-0.5.1-cp311-cp311-emscripten_3_1_45_wasm32.whl)

```bash
# outside the docker container
docker cp 293695c6e022:/src/tiktoken/dist/tiktoken-0.5.1-cp311-cp311-emscripten_3_1_45_wasm32.whl .
```

finally in index3.html we get this error
```javascript
ValueError: Can't fetch wheel from 'https://github.com/psymbio/tiktoken_rust_wasm/blob/main/packages/build_emscripten/tiktoken-0.5.1-cp311-cp311-emscripten_3_1_45_wasm32.whl'. One common reason for this is when the server blocks Cross-Origin Resource Sharing (CORS). Check if the server is sending the correct 'Access-Control-Allow-Origin' header.
```
resolve it by setting relative file path of the .whl file instead of the github link

Now we get this error:
```javascript
Uncaught (in promise) PythonError: Traceback (most recent call last):
  File "/lib/python311.zip/_pyodide/_base.py", line 499, in eval_code
    .run(globals, locals)
     ^^^^^^^^^^^^^^^^^^^^
  File "/lib/python311.zip/_pyodide/_base.py", line 340, in run
    coroutine = eval(self.code, globals, locals)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "<exec>", line 2, in <module>
  File "/lib/python3.11/site-packages/tiktoken/registry.py", line 73, in get_encoding
    enc = Encoding(**constructor())
                     ^^^^^^^^^^^^^
  File "/lib/python3.11/site-packages/tiktoken_ext/openai_public.py", line 64, in cl100k_base
    mergeable_ranks = load_tiktoken_bpe(
                      ^^^^^^^^^^^^^^^^^^
  File "/lib/python3.11/site-packages/tiktoken/load.py", line 116, in load_tiktoken_bpe
    contents = read_file_cached(tiktoken_bpe_file)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/lib/python3.11/site-packages/tiktoken/load.py", line 48, in read_file_cached
    contents = read_file(blobpath)
               ^^^^^^^^^^^^^^^^^^^
  File "/lib/python3.11/site-packages/tiktoken/load.py", line 24, in read_file
    resp = requests.get(blobpath)
           ^^^^^^^^^^^^^^^^^^^^^^
  File "/lib/python3.11/site-packages/requests/api.py", line 73, in get
    return request("get", url, params=params, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/lib/python3.11/site-packages/requests/api.py", line 59, in request
    return session.request(method=method, url=url, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/lib/python3.11/site-packages/requests/sessions.py", line 589, in request
    resp = self.send(prep, **send_kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/lib/python3.11/site-packages/requests/sessions.py", line 703, in send
    r = adapter.send(request, **kwargs)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/lib/python3.11/site-packages/requests/adapters.py", line 486, in send
    resp = conn.urlopen(
           ^^^^^^^^^^^^^
  File "/lib/python3.11/site-packages/urllib3/connectionpool.py", line 770, in urlopen
    conn = self._get_conn(timeout=pool_timeout)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/lib/python3.11/site-packages/urllib3/connectionpool.py", line 296, in _get_conn
    return conn or self._new_conn()
                   ^^^^^^^^^^^^^^^^
  File "/lib/python3.11/site-packages/urllib3/connectionpool.py", line 1061, in _new_conn
    raise ImportError(
ImportError: Can't connect to HTTPS URL because the SSL module is not available.

    at new_error (pyodide.asm.js:9:12519)
    at pyodide.asm.wasm:0x158827
    at pyodide.asm.wasm:0x15892c
    at Module._pythonexc2js (pyodide.asm.js:9:640895)
    at Module.callPyObjectKwargs (pyodide.asm.js:9:81856)
    at Proxy.callKwargs (pyodide.asm.js:9:97507)
    at Object.runPython (pyodide.asm.js:9:118859)
    at main (index3.html:14:29)
```

Also, requests library is something that doesn't work at all - look at https://github.com/pyodide/pyodide/issues/3711 (very recent issue) and developers agree on that fact

--> will resolve on 2023/10/21

## 2023/10/29 Updates
To resolve the requests library I have created my version of the code (https://github.com/psymbio/tiktoken) and added the http-pyodide patch for the requests library. Now I will take the steps again.

## 2023/10/31 Updates
I got this error:
```
pyodide.asm.js:9 Access to XMLHttpRequest at 'https://openaipublic.blob.core.windows.net/encodings/cl100k_base.tiktoken' from origin 'http://127.0.0.1:5500' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

Resolution for this is caching the weights therefore, I created a new branch called `cached_weights` in https://github.com/psymbio/tiktoken/tree/cached_weights and I'll create a new wheel using this branch and then store that wheel in the packages/build_emscripten_cached_weights/ directory and try the whole process all over again.

## 2023/11/01 Updates
I had some errors with paths of the cached_weights can across this: https://stackoverflow.com/questions/1011337/relative-file-paths-in-python-packages basically goes over how to deal with paths in a python library using `os.path.dirname(__file__)`, trying to implemenet it once more.

## Tiktoken Request Library Issues
1. Requests library dependency issue: https://www.google.com/search?q=pyodide+requests (how to use the requests library in python) lands us here: https://github.com/pyodide/pyodide/issues/398 where you can see at the bottom that @lesteve metions how scikit-bio v0.5.8 needs to be implemented with pyodide (https://github.com/pyodide/pyodide/pull/3858) and this lands us here (https://github.com/pyodide/pyodide/issues/3876) 

```
So with monekypatching in pyodide-http, requests should work. However, the question remains how we should deal with packages that have a mandatory dependency on requests.

There could be several options,

1. Try to make requests optional in the package, at least so that imports wouldn't fail if requests is not installed. Then letting users install pyodide-http and requests dependencies themselves.
2. Physically add requests to our dependency tree. So far we have been reluctant to do this since it won't work with either pyodide-http or some comparable workarounds. This would be probably the most straightforward solution, but for instance as far as I understand JupyterLite doesn't use pyodide-http in a webworker, so we need to be sure it's not breaking their approach. cc @bollwyvl
3. Same as 2 but depending on the PyPI package, instead of re-packaging the pure python wheel on our side. This functionality is not yet supported.
```
The most promising one out of all of these is in the tiktoken package we make requests an optional requirement line 9 in pyproject.toml (https://github.com/openai/tiktoken/blob/main/pyproject.toml)
```toml
dependencies = ["regex>=2022.1.18", "requests>=2.26.0"]
optional-dependencies = {blobfile = ["blobfile>=2"]}
```

changes to:
```toml
dependencies = ["regex>=2022.1.18"]
optional-dependencies = {blobfile = ["blobfile>=2"], requests = ["requests>=2.26.0"]}
```

## Relevant Links (Additional notes)
1. https://github.com/PyO3/maturin: zero configuration replacement for setuptools-rust and milksnake. It supports building wheels for python 3.7+ on windows, linux, mac and freebsd, can upload them to pypi and has basic pypy and graalpy support.
2. https://emscripten.org/docs/getting_started/downloads.html: download emscripten for your OS
3. https://github.com/pyodide/pyodide/blob/main/docs/development/new-packages.md: general process to getting a Python package working in the browser with Pyodide

## URL Journeys
1. https://discuss.python.org/t/support-wasm-wheels-on-pypi/21924/9 &rarr; https://github.com/pyodide/pyodide/issues/2816 &rarr; https://github.com/huggingface/tokenizers/issues/1010
2. https://github.com/PyO3/maturin/pull/974 &rarr; https://github.com/pola-rs/polars/issues/3672 (promising comment by @kylebarron going over the pyodide build)
<!--
Additional scrapped off notes...
## Step 1. Reinstalling Rust with Nightly Build
If you've already installed rust you probably need to reinstall it with the nightly build. Here are the steps I've taken to do the same:
```bash
# uninstall rust
rustup self uninstall -y
# install rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source $HOME/.cargo/env
rustup toolchain install nightly
rustup target add --toolchain nightly wasm32-unknown-emscripten
rustup component add rust-src --toolchain nightly-x86_64-unknown-linux-gnu
```

## Step 2. Emscripten Setup
Now we need to setup emscripten for the wasm build of the wheel
```bash
sudo apt-get install python3
sudo apt-get install cmake
sudo apt-get install git
git clone https://github.com/emscripten-core/emsdk.git
cd emsdk
git pull
./emsdk install latest
./emsdk activate latest
source ./emsdk_env.sh
``` -->

## Building Pure Python wheel for Openai
```bash
git clone -b release-v0.28.1 https://github.com/openai/openai-python.git
cd openai-python/
python -m build
```

## Building Pure Python Wheel for multidict v4.7.6 - this available in the README.rst
```bash
MULTIDICT_NO_EXTENSIONS=1 python3 setup.py bdist_wheel
```

## Building Pure Python Wheel for aiohttp
```bash
git clone https://github.com/aio-libs/aiohttp.git
cd aiohttp
git submodule update --init
export AIOHTTP_NO_EXTENSIONS=True
python3 setup.py bdist_wheel
```

## Building Pure Python Wheel for Frozenlist
```bash
git clone https://github.com/aio-libs/frozenlist.git
cd frozenlist
export FROZENLIST_NO_EXTENSIONS=True
python3 setup.py bdist_wheel
```