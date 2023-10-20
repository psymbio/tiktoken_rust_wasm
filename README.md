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
sudo apt install curl
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source $HOME/.cargo/env
rustup toolchain install nightly
rustup target add --toolchain nightly wasm32-unknown-emscripten
rustup component add rust-src --toolchain nightly-x86_64-unknown-linux-gnu

# once this is done we need to install maturin and  emsdk
# emsdk seems to install on the make step of the code too so is this required?
pip install -U maturin
pip install ./pyodide-build

# Set up emscripten 3.1.14. As of pyodide 0.21.0a3, pyodide is compiled against emscripten 3.1.14 and any extension module must also be compiled against the same version.
# https://github.com/pola-rs/polars/issues/3672
git clone https://github.com/emscripten-core/emsdk.git # tested and working at commit hash 961e66c
cd emsdk/
./emsdk install 3.1.14
./emsdk activate 3.1.14
source ./emsdk_env.sh

# https://github.com/huggingface/tokenizers/issues/1010
git clone https://github.com/openai/tiktoken.git
pip install --upgrade pip
pip install setuptools_rust
sudo apt-get install pkg-config libssl-dev
cd tiktoken
python setup.py install --user
sudo apt-get install vim
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

This should print the following:
```bash
encoding and decoding test passed!
```

```bash
# in the tiktoken directory - this builds the tiktoken wasm wheel
RUSTUP_TOOLCHAIN=nightly maturin build --release -o dist --target wasm32-unknown-emscripten -i python3.10
```

Then we need to download the wheel. So, outside the docker container terminal i.e. your own terminal run the following

```
docker ps -a
# notedown the container name that your container runs on
# now download the wheel file to your local filesystem
# for me this looked like
docker cp 293695c6e022:/src/tiktoken/dist/tiktoken-0.5.1-cp310-cp310-emscripten_3_1_14_wasm32.whl .
```

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