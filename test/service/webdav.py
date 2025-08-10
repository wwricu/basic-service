from xml.dom.minidom import parseString
from xmler import dict2xml


def test_xml_parse():
    resp_dict = {
        'multistatus': {
            '@ns': 'D',
            "@attrs": {  # @attrs takes a dictionary. each key-value pair will become an attribute
                "xmlns:D": "http://schemas.xmlsoap.org/soap/envelope/"
            },
            'response': {
                '@ns': 'D',
                "@attrs": {  # @attrs takes a dictionary. each key-value pair will become an attribute
                    "xmlns:D": "http://schemas.xmlsoap.org/soap/envelope/"
                },
            }
        }
    }
    dom = dict2xml(resp_dict)
    print(dom)
    dom = parseString(dom)
    print(dom.toprettyxml())


if __name__ == '__main__':
    test_xml_parse()
