import json

# Parse the JSON data
with open('assortiment.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

def search_products(query):
    results = []
    query = query.lower()
    
    for product, details in data.items():
        if query in product.lower():
            if details['AVAILABILITY'] == 1:
                results.append((product, details['PRICE']))
        else:
            for flavor in details:
                if isinstance(details[flavor], dict) and 'availability' in details[flavor]:
                    if query in flavor.lower() and details[flavor]['availability'] == 1:
                        results.append((f"{product} - {flavor}", details['PRICE']))
    
    return results

def main():
    while True:
        search_query = input("Enter a product name to search (or 'quit' to exit): ")
        if search_query.lower() == 'quit':
            break
        
        results = search_products(search_query)
        
        if results:
            print("\nMatching products:")
            for product, price in results:
                print(f"- {product} (Price: {price})")
        else:
            print("No matching products found.")
        print()

if __name__ == "__main__":
    main()