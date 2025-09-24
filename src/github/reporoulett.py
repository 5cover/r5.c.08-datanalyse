from reporoulette import IDSampler
from dotenv import load_dotenv
import os
import json

load_dotenv()

# Initialize the sampler
sampler = IDSampler(token=os.getenv('GITHUB_TOKEN'))

# Get 50 random repositories
repos = sampler.sample(n_samples=1000)

# Print basic stats
print(f"Success rate: {sampler.success_rate:.2f}%")
print(repos)
