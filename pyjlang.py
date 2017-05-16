import math
import argparse

variables = {}


def debug(*args):
    print("[DEBUG]", *args)


def is_power(char):
    u = str(hex(ord(char)))
    n = u[-1]
    u = u[:-1]
    if n in "129":
        return u == "0xb"
    else:
        return u == "0x207"


def get_power(char):
    u = str(hex(ord(char)))
    n = u[-1]
    if not is_power(char): return None
    return int(n)


class Terminator:
    def __str__(self):
        return "Terminator()"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return type(self) == type(other) or type(self) == other


class Power:
    def __init__(self, val):
        if type(val) == str:
            self.value = get_power(val)
        elif type(val) == int:
            self.value = val
        self.__class__ = Modifier
        self.type = val
        Modifier.modifications[val] = lambda x: x.get() ** get_power(self.type)

    def __int__(self):
        return self.value

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return self.__str__()


class Operator:
    operators = ["+", "-", "^", "*", "/", "%", "=", "."]
    operations = {
        "+": lambda x, y: x + y,
        "-": lambda x, y: x - y,
        "^": lambda x, y: x ** y,
        "*": lambda x, y: x * y,
        "/": lambda x, y: x / y,
        "%": lambda x, y: x % y,
        "=": lambda x, y: [Code.set(x.name, y), x.get()][1],
        ".": lambda x, y: [x.set(y.modify(x.get())), x.get()][1]
    }

    def __init__(self, op):
        self.type = op
        if op not in Operator.operators:
            raise TypeError("Attempted to create an operator out of string '{}'".format(op))

    def __str__(self):
        return "Operator({})".format(self.type)

    def __repr__(self):
        return self.__str__()

    def operate(self, x, y):
        print("Operation:", x, y)
        return Operator.operations[self.type](x, y)


class Functions:
    @staticmethod
    def print(*args):
        print(*(Code.get_val(arg) for arg in args[0]))


class Modifier:
    def __init__(self, type):
        self.type = type

    def __str__(self):
        return "Modifier({})".format(self.type)

    def __repr__(self):
        return self.__str__()

    def modify(self, other):
        return Modifier.modifications[self.type](other)

    modifiers = ["!"]
    modifications = {
        "!": lambda x: math.factorial(x)
    }


class Code:
    functions = {
        "print": Functions.print
    }
    java_formats = {
        "print": "System.out.println({})"
    }

    @staticmethod
    def get_val(var):
        if type(var) in [Code.Variable, Code.Function]:
            return var.name
        else:
            return var

    builtins = functions.keys()

    @staticmethod
    def set(name, val):
        global variables
        variables[name] = val

    @staticmethod
    def get(name):
        try:
            return variables[name]
        except KeyError:
            debug("Variable {} is not set".format(name))
            return None

    class Variable:
        def __init__(self, name, value=None):
            if name in Code.functions:
                self.__class__ = Code.Function
            self.name = name
            self.value = value

        def get(self):
            return Code.get(self.name)

        def set(self, val):
            Code.set(self.name, val)

        def __int__(self):
            return int(self.get())

        def __str__(self):
            return "Variable({})={}".format(self.name, self.get() if self.get() is not None else "*Not Set*")

        def __repr__(self):
            return self.__str__()

        def __add__(self, other):
            val = self.get()
            if type(val) == int:
                return int(self.get()) + other
            if type(val) == str:
                return str(self.get()) + other
            else:
                return type(other)(self.get()) + other

        def __radd__(self, other):
            val = self.get()
            if type(val) == int:
                return self.__add__(other)
            if type(val) == str:
                return other + str(self.get())
            else:
                return other + type(other)(self.get())

    class Function:
        def run(self, *args):
            print("Running:", self.name)
            Code.functions[self.name](args)
            self.run = Code.functions[self.name]

        def __init__(self, name):
            if name not in Code.functions:
                raise NameError("{} has not been declared as function".format(name))
            else:
                self.name = name
                self.run = Code.functions[name]
                self.builtin = self.name in Code.builtins

        def is_builtin(self):
            return self.builtin

        def __str__(self):
            return "Function({})".format(self.name)

        def __repr__(self):
            return self.__str__()


def decompose(code):
    """
    :param code:
    :type code: str
    :return: A list containing simplified code
    :rtype: list
    """
    place = 0
    end = []
    var = ""
    while True:
        if place > len(code) - 1:
            if var not in ["", " "]:
                end.append(Code.Variable(var))
            end.append(Terminator())
            return end
        char = code[place]
        if is_power(char):
            end.append(Power(char))
        elif char in Modifier.modifiers:
            if var not in ["", " "]:
                end.append(Code.Variable(var))
            var = ""
            end.append(Modifier(char))
        elif char in Operator.operators:
            if var != " " and var != "":
                end.append(Code.Variable(var))
            end.append(Operator(char))
            var = ""  # resets variable var
        elif char == "\\":
            place += 1
            end.append(code[place])
        elif char == "\"":
            place += 1
            c = code[place]
            string = ""
            while c != "\"":
                string += c
                place += 1
                c = code[place]
            end.append(string)
        elif char.isdecimal():
            num = int(char)
            try:
                while code[place + 1].isdecimal():
                    place += 1
                    char = code[place]
                    num = num * 10 + int(char)
            except IndexError:
                pass
            end.append(num)
        else:
            if char == " ":
                if var != " " and var != "":
                    end.append(Code.Variable(var))
                var = ""
            elif char in [";", "\n"]:
                if var != " " and var != "":
                    end.append(var)
                end.append(Terminator())
            else:
                var += char
        place += 1


def simplify(t): # Try to stop using this method
    new = []
    place = 0
    while True:
        if place >= len(t):
            for i in new:
                if type(i) == Operator or type(i) == Modifier:
                    new = simplify(new)  # recursion
            return tuple(new)
        var = t[place]
        val = None
        if type(var) == Code.Variable:
            val = var.get()
        try:
            if type(t[place + 1]) == Operator:
                op = t[place + 1]
                other = t[place + 2]
                place += 2
                var = op.operate(var, other)
            if type(t[place + 1]) == Modifier:
                modifier = t[place + 1]
                place += 1
                var = modifier.modify(val)
        except IndexError:
            pass
        place += 1
        new.append(var)


a = """\
print "hello"\\a1234\
"""


# print(a)
# print(decompose(a))
# print(decompose("1 + 2"))
# print(decompose(a))
# print("===Testing===")
# print(decompose("Hello+World"))


def run(code):
    """
    :param code: A list containing the "decomposed" code
    :type code: list
    :rtype: None
    :returns Nothing
    """
    place = 0
    print(code)
    while True:
        if place >= len(code):
            break
        variable = code[place]
        if type(variable) == Code.Variable:
            if code[place + 1] == "=":
                Code.set(variable.name, code[place + 2])
                place += 2
            elif type(code[place + 1]) == Operator:
                op = code[place + 1]
                other = code[place + 2]
                op.operate(variable, other)
        if type(variable) == Code.Function:
            if code[place + 1] == Terminator:
                variable.run()
            else:
                args = []
                place += 1
                var = code[place]
                while var != Terminator:
                    args.append(var)
                    place += 1
                    var = code[place]
                variable.run(*simplify(args))
        place += 1


def javafy(args):
    nargs = []
    for arg in args:
        if hasattr(arg, "get_java_method"):
            nargs.append(arg.get_java_method())
        elif type(arg) == Code.Variable:
            nargs.append(arg.name)

        elif type(arg) != str:
            nargs.append(str(arg))
    return nargs


class JavaTools:
    @staticmethod
    def simplify(t):
        new = []
        place = 0
        while True:
            if place >= len(t):
                for i in new:
                    if type(i) == Operator or type(i) == Modifier:
                        new = JavaTools.simplify(new)  # recursion
                return tuple(new)
            var = t[place]
            val = None
            if type(var) == Code.Variable:
                val = var
            try:
                if type(t[place + 1]) == Operator:
                    op = t[place + 1]
                    other = t[place + 2]
                    place += 2
                    var = ParserElements.Operation(op.type, var, other)
                    # if type(t[place + 1]) == Modifier:  # Not implemented properly
                    # modifier = t[place + 1]
                    # place += 1
                    # var = modifier.modify(val)
            except IndexError:
                pass
            place += 1
            new.append(var)


class ParserElements:
    class RuntimeFunction(Code.Function):
        def __init__(self, function, args=()):
            super().__init__(function.name)
            self.function = function
            self.args = args

        def has_java_method(self):
            return self.is_builtin()

        def get_java_method(self):
            if self.is_builtin():
                return Code.java_formats[self.name].format(', '.join(javafy(JavaTools.simplify(self.args))))

        def run(self):
            return self.function.run(self.args)

    class Assignment:
        def __init__(self, name, val):
            self.name = name
            self.value = val

    class Operation:
        def __init__(self, operator, a, b):
            """

            :param operator:
            :param a:
            :param b:
            :type a: Code.Variable
            :type b: Code.Variable
            """
            self.operator = operator
            self.a = a
            self.b = b

        def get_java_method(self):
            return self.__str__()

        def __repr__(self):
            return self.__str__()

        def __str__(self):
            bv = self.b
            av = self.a
            if type(bv) == Code.Variable:
                bv = bv.name
            if type(av) != Code.Variable:
                debug("the {a} in the assignment {a}={b} is not a variable".format(a=av, b=bv))
            else:
                av = av.name

            return "{a} {op} {b}".format(a=av, b=bv, op=self.operator)


def parse(code):
    """
    :param code: A list containing the "decomposed" code
    :type code: list, str
    :rtype: list
    """
    code = decompose(code) if type(code) == str else code
    place = 0
    parsed = []
    while True:
        if place >= len(code):
            break
        variable = code[place]
        if type(variable) == Code.Variable:
            if code[place + 1] == "=":
                # Code.set(variable.name, code[place + 2])
                parsed.append(ParserElements.Assignment(variable.name, code[place + 2]))
                place += 2
            elif type(code[place + 1]) == Operator:
                pass  # Java doesn't really do anything with alone statements
                # op = code[place+1]
                # other = code[place+2]
                # op.operate(variable, other)
                # # parsed.append(op)
        if type(variable) == Code.Function:
            if code[place + 1] == Terminator:
                # variable.run()
                parsed.append(ParserElements.RuntimeFunction(variable))
            else:
                args = []
                place += 1
                var = code[place]
                while var != Terminator:
                    args.append(var)
                    place += 1
                    var = code[place]
                parsed.append(ParserElements.RuntimeFunction(variable, args))
                # variable.run(*simplify(args))
        place += 1
    return parsed


def compile_java(parsed):
    """

    :param parsed:
    :type parsed: list
    :return:
    """
    java = """\
    {methods}
package me.ezeh.MathLang
public static void main(String args[]){{
    {main}
}}
"""
    methods = ""
    main = ""
    for variable in parsed:
        if type(variable) == ParserElements.RuntimeFunction:
            if variable.has_java_method:
                main += variable.get_java_method() + ";"
            else:
                print("[Error] function {} does not have a java equivalent".format(variable.name))
                exit()
    return java.format(methods=methods, main=main)


def run_code(code):
    return run(decompose(code))


def run_file(file):
    f = open(file, "r")
    assert f.readable()
    run_code(f.read())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run Mathlang.')
    parser.add_argument("--java", help="Write  output a java  source file",
                        action="store_true")
    parser.add_argument("--output", type=str, default=None)
    parser.add_argument("--finput", action="store_true")
    parser.add_argument("code", type=str, default=None)
    args = parser.parse_args()
    code = ""
    if args.finput:
        # f = open(parser.finput, "r")
        # code = f.read()
        run_file(args.finput)
    else:
        if args.code is None:
            parser.error("the following arguments are required: code")
        code = args.code
    if args.java:
        print(compile_java(parse(code)))
    else:
        run_code(code)
