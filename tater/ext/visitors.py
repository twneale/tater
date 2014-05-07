from tater.base.visitor import Visitor


class DataVisitor(Visitor):

    def get_nodekey(self, obj):
        return obj.__class__.__name__

    def get_children(self, obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                yield k
                yield v
        if isinstance(obj, (list, tuple, set, frozenset)):
            for thing in obj:
                yield thing
        else:
            return

    def visit_dict(self, obj):
        for item in obj.items():
            self.visit_dict_item(*item)

    def visit_list(self, obj):
        for item in obj:
            self.visit(item)

    visit_tuple = visit_set = visit_list
