from tater import Node, matches, matches_subtypes


class Root(Node):

    @matches('Comment')
    def handle_comment(self, comment):
        return self.descend('Comment', comment)

    @matches('Symbol', 'Operator.Equals')
    def handle_assign(self, symbol, equals):
        assign = self.descend('Assignment')
        assign.descend('Symbol', symbol)
        return assign.descend('Production')

    @matches('Semicolon')
    def handle_sem(self, *items):
        return self


class Tok(Node):

    @matches_subtypes('Operator')
    def handle_concat(self, operator):
        name = operator.token.replace('Operator.', '')
        return self.swap(name)


class String(Tok):
    pass


class Symbol(Tok):
    pass


class Expression(Tok):

    @matches('String')
    def handle_string(self, string):
        return self.descend('String', string)

    @matches('Symbol')
    def handle_symbol(self, *items):
        return self.descend('Symbol', items)

    @matches('Repeat.Start')
    def handle_repeat(self, *items):
        return self.descend('Repeat')

    @matches('Option.Start')
    def handle_option(self, *items):
        return self.descend('Option')

    @matches('Group.Start')
    def handle_group(self, *items):
        return self.descend('Group')


class Concat(Expression):
    pass


class Repeat(Expression):
    @matches('Repeat.End')
    def handle_end(self, *items):
        return self.pop()


class Option(Expression):
    @matches('Option.End')
    def handle_end(self, *items):
        return self.pop()


class Group(Expression):
    @matches('Group.End')
    def handle_end(self, *items):
        return self.pop()


class Production(Expression):
    pass

