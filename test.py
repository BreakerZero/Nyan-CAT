import torch
torch.cuda.empty_cache()
from transformers import AutoModelForCausalLM, AutoTokenizer, set_seed
torch.set_default_tensor_type(torch.FloatTensor)
device = "cpu"
model = AutoModelForCausalLM.from_pretrained("bigscience/bloom-1b3", use_cache=True)
tokenizer = AutoTokenizer.from_pretrained("bigscience/bloom-1b3")
set_seed(51675)

prompt = 'Salut!, Je suis'

input_ids = tokenizer(prompt, return_tensors="pt").to(device)

sample = model.generate(**input_ids, max_length=50, top_k=0, temperature=0.7, repetition_penalty=1.2)

print(tokenizer.decode(sample[0], truncate_before_pattern=[r"\n\n^#", "^'''", "\n\n\n"]))

