import random

# Create a list of 10 random numbers between 1 and 20.
rand_list = [random.randint(1,20) for _ in range(10)]

# Filter Numbers Below 10 (List Comprehension)
list_comprehension_below_10 = [i for i in rand_list if i < 10]

# Filter Numbers Below 10 (Using filter)
list_comprehension_below_10 = list(filter(lambda a: a < 10, rand_list))

print(f"list of 10 random numbers between 1 and 20 {rand_list}")
print(f"Filter Numbers Below 10 (List Comprehension): {list_comprehension_below_10}")
print(f"Filter Numbers Below 10 (Using filter) {list_comprehension_below_10}")
