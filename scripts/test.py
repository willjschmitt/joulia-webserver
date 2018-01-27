import re

txt = 'High (10 - 15%)'
tolerances = re.match(
        r'.*\((?P<low_abv>\d+) - (?P<high_abv>\d+)\s*%\)', txt)
print(tolerances)
