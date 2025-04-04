from wwricu.service.storage import oss

# oss.list_all()
def test_this():
    for obj in oss.list_page(page_size=2):
        print(obj.model_dump())
