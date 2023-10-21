from tokenizers import Tokenizer
tokenizer = Tokenizer.from_file("./tokenizer.json")
encoded = tokenizer.encode("I can feel the magic, can you?")
print(encoded.ids)
print(encoded.tokens)
