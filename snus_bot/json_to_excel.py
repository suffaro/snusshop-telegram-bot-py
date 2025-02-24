import json
import pandas as pd

def flatten_json(json_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    flattened_data = []
    for snus_name, snus_info in data.items():
        snus_price = snus_info.get('PRICE', '')
        snus_availability = snus_info.get('AVAILABILITY', '')
        
        for flavor, flavor_info in snus_info.items():
            if isinstance(flavor_info, dict):
                flattened_data.append({
                    'SNUS_NAME': snus_name,
                    'SNUS_FLAVOR': flavor,
                    'amount': flavor_info.get('amount', ''),
                    'availability': flavor_info.get('availability', ''),
                    'PRICE': snus_price,
                    'AVAILABILITY': snus_availability
                })
    
    return flattened_data

def json_to_excel(json_file, excel_file):
    flattened_data = flatten_json(json_file)
    df = pd.DataFrame(flattened_data)
    
    # Reorder columns
    column_order = ['SNUS_NAME', 'SNUS_FLAVOR', 'amount', 'availability', 'PRICE', 'AVAILABILITY']
    df = df[column_order]
    
    df.to_excel(excel_file, index=False)
    print(f"Excel file '{excel_file}' created successfully.")

def excel_to_json(excel_file, json_file):
    # Read Excel file
    df = pd.read_excel(excel_file)
    
    # Initialize the JSON structure
    json_data = {}
    
    # Iterate through DataFrame rows
    for _, row in df.iterrows():
        snus_name = row['SNUS_NAME']
        flavor = row['SNUS_FLAVOR']
        
        # If this is a new SNUS_NAME, initialize its dictionary
        if snus_name not in json_data:
            json_data[snus_name] = {
                'PRICE': row['PRICE'],
                'AVAILABILITY': row['AVAILABILITY']
            }
        
        # Add flavor information
        json_data[snus_name][flavor] = {
            'amount': row['amount'],
            'availability': row['availability']
        }
    
    # Write to JSON file
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=4)
    
    print(f"JSON file '{json_file}' created successfully.")


def sort_json():
    import json

# Read the JSON data from the file
    with open('assortiment.json', 'r', encoding='utf-8') as file:
        data = json.load(file)

    # Sort the data by main key
    sorted_data = dict(sorted(data.items()))

    # Save the sorted data back to the file
    with open('sorted_assortiment.json', 'w', encoding='utf-8') as file:
        json.dump(sorted_data, file, indent=4, ensure_ascii=False)

    print("JSON data has been sorted and saved to 'sorted_assortiment.json'")



# Usage
def main():
    selection = input("Enter 1 to convert JSON to Excel, 2 to convert Excel to JSON, 3 to sort JSON: ")
    if selection == '1':
        json_to_excel('assortiment.json', 'output.xlsx')
    elif selection == '2':
        excel_to_json('output.xlsx', 'assortiment.json')
    elif selection == '3':
        sort_json()
    else:
        print("Invalid input. Please enter 1 or 2.")

main()
