import zipfile
import xml.etree.ElementTree as ET
import csv

def extract_listone():
    archive = 'lista_calciatori_lista calciatori_classic_ii-fantaremo.xlsx'
    
    with zipfile.ZipFile(archive, 'r') as z:
        with z.open('xl/worksheets/sheet1.xml') as f:
            tree = ET.parse(f)
            root = tree.getroot()
            
            # Namespace map usually required for openxml
            ns = {'ns': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
            
            with open('listone.csv', 'w', newline='', encoding='utf-8') as out:
                writer = csv.writer(out)
                
                sheetData = root.find('ns:sheetData', ns)
                if not sheetData:
                    print("Could not find sheetData")
                    return
                
                for row in sheetData.findall('ns:row', ns):
                    row_data = []
                    for c in row.findall('ns:c', ns):
                        v = c.find('ns:v', ns)
                        if v is not None:
                            row_data.append(v.text)
                        else:
                            row_data.append('')
                    writer.writerow(row_data)

extract_listone()
