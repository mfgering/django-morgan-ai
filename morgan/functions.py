import openai
try:
    from morgan.dawson_deeds import *
except Exception:
    try:
        from dawson_deeds import *
    except Exception:
        from .dawson_deeds import *
from django.contrib.staticfiles.storage import staticfiles_storage

class UnitInfo(object):
    def __init__(self) -> None:
        (self._assignments_header, self._assignments) = self._make_map('unit_assignments.txt')
        (self._interest_header, self._interest) = self._make_map('unit_interest.txt')
        (self._real_estate_id_header, self._real_estate_id) = self._make_map('unit_real_estate_id.txt')

    def _get_file_contents(self, filename):
        content = None
        try:
            path = staticfiles_storage.path(f'files/{filename}')
            os.path.isfile(path)
        except:
            path = f"./morgan/static/files/{filename}"
            os.path.isfile(path)
        with open(path, 'r') as fp:
            content = fp.readlines()
        return content
    
    def _make_map(self, filename):
        map = {}
        content = self._get_file_contents(filename)
        #header
        header = content[0].split('|')[1:-1]
        # units
        for unit_line  in content[2:]:
            a = unit_line.split('|')[1:]
            map[a[0]] = a[1:-1]
        return header, map

    def _unit2prop(self, unit, prop):
        u_val = str(unit).strip()
        # Look for prop in the headers
        hdr_map = [(self._assignments_header, self._assignments),
                   (self._interest_header, self._interest),
                   (self._real_estate_id_header, self._real_estate_id)]
        for hdr, tbl in hdr_map:
            if prop in hdr:
                val = tbl[u_val][hdr.index(prop)-1]
                return val
        return None
    
    def is_valid_unit(self, unit):
        u_val = str(unit).strip()
        for m in [self._assignments, self._interest, self._real_estate_id]:
            if u_val in m.keys():
                return True
        return False

    def real_estate_id_2_unit(self, real_estate_id):
        clean = str(real_estate_id).strip()
        key = next((k for k, v in self._real_estate_id.items() if v[0] == clean), None)
        return key

    def get_props(self):
        props = self._assignments_header[1:]+self._interest_header[1:]+self._real_estate_id_header[1:]
        return props

    
def get_unit_info(unit, prop):
    unit_info = UnitInfo()
    val = unit_info._unit2prop(unit, prop)
    return val

def get_deed_info(real_estate_id):
    # Check that the real_estate_id is valid
    unit_info = UnitInfo()
    result = {}
    unit = unit_info.real_estate_id_2_unit(real_estate_id)
    if unit is not None:
        apt = Apt(real_estate_id, '000')
        result['owner'] = str(apt.owner)
        result['deed_date'] = str(apt.deed_date)
        result['pkg_sale_price'] = str(apt.pkg_sale_price)
        result['assessed'] = str(apt.assessed)
    return result

tool_get_deed_info_defn = """
{
    "name": "get_deed_info",
    "description": "Get deed information from Wake County",
    "parameters":
    {
        "type": "object",
        "properties":
        {
            "real_estate_id":
            {
                "type": "string",
                "description": "Real estate id from Wake County"
            }
        },
        "required": ["real_estate_id"]
    }
}
"""

tool_get_deed_info_defn = """
{
    "name": "get_unit_info",
    "description": "Get information for a unit",
    "parameters":
    {
        "type": "object",
        "properties":
        {
            "unit":
            {
                "type": "string",
                "description": "Unit identifier"
            },
           "prop":
            {
                "type": "string",
                "enum": [
                    "Parking Space",
                    "Storage Locker",
                    "Personal Lock Box",
                    "unit type",
                    "approximate square footage",
                    "residential percent interest",
                    "commercial percent interest",
                    "total percent interest",
                    "real_estate_id"
                ],
                "description": "Unit property to look up"
            }
             
        },
        "required": ["unit", "prop"]
    }
}
"""

if __name__ == "__main__":
    unit_info = UnitInfo()
    unit = unit_info.real_estate_id_2_unit('0328656')
    is_valid = unit_info.is_valid_unit(117)
    props = unit_info.get_props()
    q = [f'"{prop}"' for prop in props]

    props_str = ",\n".join(q)
    print(props_str)
    unit = 410
    info = get_unit_info(unit)
    v = info._unit2prop(412, 'Parking Space')
    acct_id = '0329082'
    info = get_deed_info(acct_id)
    print(info)