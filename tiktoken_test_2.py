import tiktoken
enc = tiktoken.get_encoding("cl100k_base")
if (enc.decode(enc.encode("hello world")) == "hello world"):
    print("encoding and decoding test passed!")
else:
    print("encoding and decoding test failed...")

# To get the tokeniser corresponding to a specific model in the OpenAI API:
enc = tiktoken.encoding_for_model("gpt-4")