class Hyper:
    def get_keys(self):
        return self.__dict__


class Base(Hyper):
    def dict(self):
        res = dict()
        for key in self.get_keys():
            val = getattr(self, key, None)
            if val is not None:
                res.update({key: val})
        return res


class Magic(Base):
    a: str = 'test'
    b: int = 0
    c: list = ['test', 'list']


if __name__ == '__main__':
    m = Magic()
    m.a = '111'
    m.b = 3
    m.c = ['after']
    print(m.dict())
    print(m.__dict__)
