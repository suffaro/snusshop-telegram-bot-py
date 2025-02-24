import json

# with open('assortiment.json', 'r', encoding='utf-8') as file:
#     snus_assortment = json.load(file)


# # for key in snus_assortment:
# #     snus_assortment[key]["AVAILABILITY"] = 1

# with open('assortiment.json', 'w', encoding='ascii') as file:
#     json.dump(snus_assortment, file, indent=4, ensure_ascii=False)



def json_to_txt(json_file, txt_file):
    # Read the JSON file
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Write to text file with indentations
    with open(txt_file, 'w', encoding='utf-8') as f:
        write_dict(data, f)

def write_dict(d, f, indent=0):
    for key, value in d.items():
        f.write('    ' * indent + str(key) + ': ')
        if isinstance(value, dict):
            f.write('\n')
            write_dict(value, f, indent + 1)
        else:
            f.write(str(value) + '\n')

def hmmm():

# Load the JSON data
    with open('assortiment.json', 'r', encoding='utf-8') as file:
        data = json.load(file)

    # Iterate through all snus brands and flavors
    for brand, brand_data in data.items():
        for flavor, flavor_data in brand_data.items():
            if isinstance(flavor_data, dict) and 'amount' in flavor_data:
                flavor_data['amount'] = 10

    # Save the updated data back to the file
    with open('assortiment.json', 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

    print("All snus flavor amounts have been set to 10.")


if __name__ == '__main__':
    # json_file = 'assortiment.json'
    # txt_file = 'assortiment.txt'
    # json_to_txt(json_file, txt_file)
    # my_d : dict = {}

    # with open('assortiment.json', 'r', encoding='utf-8') as f:
    #     my_d = json.load(f)
    # print(my_d.keys())
    # print(len(my_d.keys()))
    hmmm()
        