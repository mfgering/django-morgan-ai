import openai
try:
    from dawson_deeds import *
except Exception:
    from .dawson_deeds import *

def get_deed_info(real_estate_id):
    result = {}
    apt = Apt(real_estate_id, '000')
    print(apt)
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

if __name__ == "__main__":
    acct_id = '0329082'
    info = get_deed_info(acct_id)
    print(info)