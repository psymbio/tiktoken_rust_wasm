# Emscripten Setup for Python+Rust (non-pure Python) Packages

The following steps are for the Linux environment.

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

## URL Journey
https://discuss.python.org/t/support-wasm-wheels-on-pypi/21924/9 &rarr; https://github.com/pyodide/pyodide/issues/2816 &rarr; https://github.com/huggingface/tokenizers/issues/1010
