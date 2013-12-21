from tater import new_basenode, matches


Node = new_basenode()


class PhoneInfo(Node):

    @matches('Extension')
    def handle_ext(self, *items):
        return self.descend('Extension', items)

    @matches('PhoneNumber')
    def handle_phonenum(self, *items):
        return self.descend('PhoneNumber', items)

    @matches('AreaCode')
    def handle_areacode(self, *items):
        return self.descend('AreaCode', items)


class AreaCode(Node):

    def in_sanfrancisco(self):
        return '415' in self.first_text()