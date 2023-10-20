# Tiktoken Python+Rust (non-pure Python) WASM

## Preliminary Notes
1. https://stackoverflow.com/questions/65185874/is-it-possible-to-build-python-wheel-in-browser-using-wasm-for-pyodide basically we can install wheels using micropip - this issue however wants to take it one step forward by building a wheel using pyodide.
2. https://stackoverflow.com/questions/52214136/how-do-i-deploy-a-python-wheels-package-statically-on-a-custom-cdn-server
There's no need to deploy using CDN, or pypiserver - just upload the wheel file on github and download using the link.
3. https://pypi.org/project/pypiserver (basically allows you to create a server and upload wheel files but this isn't needed as you simply use github to upload and download from there.). The steps to use this can be found in this [video](https://www.youtube.com/watch?v=UCY12pGM4oM&ab_channel=AustinTechLive) and the documentation.

## Documentation on the actual issue
1. https://discuss.python.org/t/support-wasm-wheels-on-pypi/21924/8 (Google search: "python wheel webassembly" resulted in this)
This comment in the discussion is important:
```
There are docs about it here . As far as I know for now the only Python package with Rust extensions we build is cryptography (but that uses setuptools-rust). There was some work on building tokenizers with mathurin in pyodide#2816 . @hoodmane who worked on this, might know more.
```
2. https://micropip.pyodide.org/en/stable/project/usage.html
They actually state the problem here:
```
If a package has C-extensions (or any other compiled codes like Rust), it will not have a pure Python wheel on PyPI.

Trying to install such a package with micropip.install will result in an error like:

ValueError: Can't find a pure Python 3 wheel for 'tensorflow'.
See: https://pyodide.org/en/stable/usage/faq.html#micropip-can-t-find-a-pure-python-wheel
You can use `await micropip.install(..., keep_going=True)` to get a list of all packages with missing wheels.
To install such a package, you need to first build a Python wheels for WASM/Emscripten for it.

Note that pyodide provides several commonly used packages with pre-built wheels. Those packages can be installed with micropip.install("package-name").
```
3. https://pyodide.org/en/stable/development/new-packages.html
```
Rust/PyO3 Packages
We currently build cryptography which is a Rust extension built with PyO3 and setuptools-rust. It should be reasonably easy to build other Rust extensions. If you want to build a package with Rust extension, you will need Rust >= 1.41, and you need to set the rustup toolchain to nightly, and the target to wasm32-unknown-emscripten in the build script as shown here, but other than that there may be no other issues if you are lucky.

As mentioned here, by default certain wasm-related RUSTFLAGS are set during build.script and can be removed with export RUSTFLAGS="".

If your project builds using maturin, you need to use maturin 0.14.14 or later. It is pretty easy to patch an existing project (see projects/fastparquet/meta.yaml for an example)

So I downloaded emscripten
https://emscripten.org/docs/getting_started/downloads.html#installation-instructions-using-the-emsdk-recommended
```

Code:

```bash
sudo apt-get install python3
sudo apt-get install cmake
sudo apt-get install git
git clone https://github.com/emscripten-core/emsdk.git
cd emsdk
git pull
# Download and install the latest SDK tools.
./emsdk install latest
# Make the "latest" SDK "active" for the current user. (writes .emscripten file)
./emsdk activate latest
# Activate PATH and other environment variables in the current terminal
source ./emsdk_env.sh
# verify the emscripten version
```

From ![here](https://discuss.python.org/t/support-wasm-wheels-on-pypi/21924/8) you end up here: https://github.com/pyodide/pyodide/issues/2816 which highlights the exact steps to take to set this up:
```
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source $HOME/.cargo/env
rustup toolchain install nightly
rustup target add --toolchain nightly wasm32-unknown-emscripten
rustup component add rust-src --toolchain nightly-x86_64-unknown-linux-gnu
sudo pip install maturin==0.13.0b8
git clone --depth 1 --branch 3.1.14 https://github.com/emscripten-core/emsdk
cd emsdk
./emsdk install latest
./emsdk activate latest
source ./emsdk_env.sh
cd ../bindings/python
RUSTUP_TOOLCHAIN=nightly maturin build --release -o dist --target wasm32-unknown-emscripten -i python3.10
```

## Real examples of the issue
1. Do have a look at this work that he did for tokenizers: https://github.com/josephrocca/tokenizers/tree/pyodide and https://github.com/josephrocca/tokenizers-pyodide
2. Another related issue: https://github.com/huggingface/tokenizers/issues/1010
3. Getting this to work, understanding micropips, wheels and working with python on the web: https://www.youtube.com/watch?v=iJmQIfmtfVk&ab_channel=MattCodes and https://www.youtube.com/watch?v=zjtQZkKV1zA&ab_channel=MattCodes
4. Another relevant path (look at this on 20th October 2023):
https://pyodide.org/en/stable/development/building-and-testing-packages.html#building-and-testing-packages-out-of-tree
https://pyodide.org/en/stable/development/building-and-testing-packages.html#building-and-testing-packages-out-of-tree

Error in index.html: Wheel platform 'linux_x86_64' is not compatible with Pyodide's platform 'emscripten-3.1.45-wasm32'
Related issues: https://github.com/pypa/cibuildwheel/issues/1002

