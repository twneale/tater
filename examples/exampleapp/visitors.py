from tater import Visitor


class PhoneInfoVisitor(Visitor):

    def __init__(self):
        self.data = {}

    def visit_PhoneNumber(self, node):
        self.data['phone_number'] = node.first_text()

    def visit_AreaCode(self, node):
        areacode = node.first_text()
        self.data['area_code'] = areacode
        if node.in_sanfrancisco():
            self.data['weather'] = 'good'

    def visit_Extension(self, node):
        self.data['ext'] = node.first_text()

    def finalize(self):
        return self.data
