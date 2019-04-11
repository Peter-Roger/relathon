"""This module describes a class for each builtin function of relathon
as well as a function object for custom defined functions."""

from abc import ABC, abstractmethod
from pyrel import Relation
from errors import ArityException, TypeException
from environment import Environment


class Callable(ABC):
    """Abstract base class for all Relathon functions.

    Attributes:
        name (str) - function name
        arity - function arity; can be none, an int, tuple, or a list
                to indicate nullary, n-ary, variadic (range), or a variable of
                aritites
        parameters (list) - the function parameters
    """

    def __init__(self, name, arity):
        self.name = name
        self.arity = arity # (minimum required, maximum possible)
        self.parameters = NotImplemented

    def checkArity(self, callstack, args):
        """Ensures that the number of arguments passed to a function
        call matches the arity (number of parameters) of the function.

        Returns:
            True - correct

        Rasies:
            ArityException - incorrect
        """
        valid = True
        if len(self.arity) == 1:
            # Variadic; accept any number of args
            pass
        elif len(args) in range(self.arity[0], self.arity[1] + 1):
            pass
        else:
            raise ArityException(callstack, self.name, self.arity, self.parameters, args)
        return True

    @abstractmethod
    def call(self, callstack, args, *more):
        """Call function abstraction method."""
        self.checkArity(callstack, args)


class Function(Callable):
    """Object for custom functions defined within Relathon."""

    def __init__(self, name, parameters, statements):
        """
        Attributes:
            parameters - list of the function parameters
            statements - the body of the function
            interpreter - the interpreter
        """
        arity = (len(parameters), len(parameters))
        super().__init__(name, arity)
        self.parameters = parameters
        self.statements = statements

    def call(self, callstack, args):
        super().call(callstack, args)
        env = Environment(
            name=self.name,
        )
        for param, arg in zip(self.parameters, args):
            env.define(param, arg)
        return env

class NewFunction(Callable):
    """Inbuilt new function. Creates a new relation.

    new(rows, cols, *bits):
        rows, cols (int) - denote the dimension;
        bits (OrderedPairs) - denotes the bits to initialize as True;
                              default is empty relation

    new(rel, *bits):
        rel (Relation) - dimenions will be the same as rel
        bits (OrderedPairs) - denotes the bits to initialize as True;
                              default is empty relation
    """

    def __init__(self, context):
        arity = (2,3)
        super().__init__("new", arity)
        self.context = context
        self.overload = (['rows', 'cols', 'bits'], ['rel', 'bits'])
        self.parameters = self.overload[0]

    def call(self, callstack, args):
        super().checkArity(callstack, args)
        if type(args[0]) == Relation:
            self.arity = (1,2)
            self.parameters = self.overload[1]
            super().call(callstack, args)
            try:
                args = (args[0].rows, args[0].cols, args[1].pairs)
            except IndexError:
                args = (args[0].rows, args[0].cols)
            except AttributeError:
                raise TypeException(callstack, callstack[-1].location, self.name, "bits argument must be an OrderedPair.")
        else:
            super().call(callstack, args)
            if type(args[0]) == int and type(args[1]) == int:

                try:
                    if args[2].__class__.__name__ != "OrderedPairs":
                        raise TypeException(callstack, callstack[-1].location, self.name, "bits argument must be an OrderedPair.")
                    else:
                        args = (args[0], args[1], args[2].pairs)
                except IndexError:
                    pass

        rel_args = tuple(args)
        return self.context.new(*rel_args)


class VectorFunction(Callable):
    """Inbuilt Vector function. Creates a new vector relation.

    vec(rows, cols, ~vec)
        rows, cols (int) - denote the dimension;
        vec (int) - if provided denotes the vector element,
                    default is first element

    vec(rel, ~vec):
        rel (Relation) - dimenions will be the same as rel
        vec (int) - if provided denotes the vector element,
                    default is first element
    """

    def __init__(self, context):
        arity = (2,3)
        super().__init__("vec", arity)
        self.context = context
        self.overload = (['rows', 'cols', 'vec'], ['rel', 'vec'])
        self.parameters = self.overload[0]

    def call(self, callstack, args):
        super().checkArity(callstack, args)
        kwargs = {'rows': 1, 'cols': 1, 'vec': 0}
        if type(args[0]) == Relation: # vec(rel, *vec):
            self.arity = (1,2)
            self.parameters = self.overload[1]
            super().call(callstack, args)
            try:
                kwargs['rows'] = args[0].rows
                kwargs['cols'] = args[0].cols
                if isinstance(args[1], int):
                    kwargs['vec'] = args[1]
                else:
                    raise TypeError
            except IndexError:
                pass
            except (AttributeError, TypeError):
                raise TypeException(callstack, callstack[-1].location, self.name, "vec argument must be an int.")
        else: # vec(rows, cols, ~vec)
            super().call(callstack, args)
            try:
                if not all(isinstance(arg, int) for arg in args):
                    raise TypeException(callstack, callstack[-1].location, self.name, "vec argument must be an int.")
                kwargs['rows'] = args[0]
                kwargs['cols'] = args[1]
                kwargs['vec'] = args[2]
            except IndexError:
                pass

        rel = self.context.new(kwargs['rows'], kwargs['cols'])
        rel.vector(vector=kwargs['vec'])
        return rel

class CopyFunction(Callable):
    """Inbuilt copy function. Creates a copy of a relation."""

    def __init__(self, context):
        arity = (1,1)
        super().__init__("copy", arity)
        self.context = context

    def call(self, callstack, args):
        super().call(callstack, args)
        relation = args[0]
        return relation.copy()


class RandomFunction(Callable):
    """Inbuilt random function. Creates a new random relation."""

    def __init__(self, context):
        arity = (1,3)
        super().__init__("random", arity)
        self.context = context
        self.parameters = ['relation', 'row', 'col']

    def call(self, callstack, args):
        super().call(callstack, args)
        relation = None
        rel_args = []
        prob_arg = []

        if len(args) > 0:
            if isinstance(args[0], Relation) and len(args) < 3:
                relation = args[0]
                len(args) == 2 and prob_arg.append(args[1])
            elif isinstance(args[0], int) and isinstance(args[1], int):
                rel_args = [args[0], args[1]]
                len(args) == 3 and prob_arg.append(args[2])
            else:
                raise TypeException(self.callstack, self.callstack[-1].location, self.name, "Invalid arguments passed to random function.")
        if prob_arg and not isinstance(prob_arg[0], float):
            raise TypeException(self.callstack, self.callstack[-1].location, self.name, "Probability argument must be a float.")

        if not relation:
            relation = self.context.new(*rel_args)
        relation.random(*prob_arg)
        return relation


class SetBitsFunction(Callable):
    """Inbuilt setbits function. Sets bits in relation."""

    def __init__(self):
        arity = (2,2)
        super().__init__("set", arity)
        self.parameters = ['relation', 'bits']

    def call(self, callstack, args, yesno=True):
        super().call(callstack, args)
        if type(args[0]) == Relation and args[1].__class__.__name__ == "OrderedPairs":
            relation, bits = args[0], args[1].pairs
            relation.set_bits(bits, yesno)
        else:
            # if not yesno:
                # self.name = "un" + self.name
            msg = "{}() arguments must be a Relation and a OrderedPair, not {} and {}".format(self.name, args[0].__class__.__name__, args[1].__class__.__name__)
            raise TypeException(self.callstack, self.callstack[-1].location, self.name, msg)


class UnsetBitsFunction(Callable):
    """Inbuilt unsetbits function. Unsets bits in relation."""

    def __init__(self):
        arity = (2,2)
        super().__init__("unset", arity)
        self.parameters = ['relation', 'bits']

    def call(self, callstack, args):
        SetBitsFunction().call(callstack, args, yesno=False)


class SetCharsFunction(Callable):
    """Inbuilt setchars function. Changes chars that represent set
    and unset bits when relation is printed."""

    def __init__(self):
        arity = (2,2)
        super().__init__("setchars", arity)
        self.parameters = ['one_ch', 'zero_ch']

    def call(self, callstack, args):
        super().call(callstack, args)
        if isinstance(args[0], str) and isinstance(args[1], str):
            one_ch, zero_ch = args[0][1:-1], args[1][1:-1]
            Relation.one_ch = one_ch
            Relation.zero_ch = zero_ch
        else:
            raise TypeException(callstack, callstack[-1].location, self.name,"{}() arguments must both be single characters, not {} and {}".format(self.name, args[0].__class__.__name__, args[1].__class__.__name__))


class PrintFunction(Callable):
    """Inbuilt print function"""

    def __init__(self):
        arity = (0,) # 0 to inf
        super().__init__("print", arity)

    def call(self, callstack, args):
        super().call(callstack, args)
        print(*args,sep='\n')


class ConstantFunction(Callable):
    """Parent Class for constant relations such as the Empty relation,
    Universal relation, and Identity relation."""

    def __init__(self, name, context, constant):
        """
        Args:
            constant - the function that returns the relation constant
            context - the relation context
        """
        arity = (1,2)
        self.context = context
        self.constant = constant
        super().__init__(name, arity)
        self.parameters = ['relation', 'row', 'col']

    def call(self, callstack, args):
        """Constant function takes a relation and returns the corresponding
        relation constant of the same dimension.

        Alternatively, two integers can be passed to denote the desired dimension and the relation constant of that size will is returned.
        """
        super().call(callstack, args)
        error = False
        try:
            arg0, arg1 = args[0], args[1]
            rows, cols = int(arg0), int(arg1)
        except TypeError:
            error = True
        except IndexError:

            try:
                relation = args[0]
                assert type(relation) == Relation
            except AssertionError:
                error = True
        else:
            relation = self.context.new(rows, cols)
        finally:
            if error:
                msg = "{}() expects either a relation or two ints for " \
                "the dimension.".format(self.name)
                raise TypeException(callstack, callstack[-1].location, self.name, self.msg)
            else:
                return self.constant(relation)


class EmptyFunction(ConstantFunction):
    """Inbuilt empty function. Creates a new empty relation."""

    def __init__(self, context):
        super().__init__("O", context, Relation.empty)

class UniversalFunction(ConstantFunction):
    """Inbuilt universal function. Creates a new universal relation."""

    def __init__(self, context):
        super().__init__("L", context, Relation.universal)

class IdentityFunction(ConstantFunction):
    """Inbuilt indentity function. Creates a new identity relation."""

    def __init__(self, context):
        super().__init__("I", context, Relation.identity)

class IsEmptyFunction(Callable):
    """Tests if a relation is Empty, that is, equal to the Empty Relation."""
    def __init__(self, true, false):
        """
        Args:
            true - True Relation defined in the interpreter's PyrelContext
            false - False Relation defined in the interpreter's PyrelContext
        """
        arity = (1,1)
        super().__init__('empty', arity)
        self.parameters = ['relation']
        self.rel_true = true
        self.rel_false = false

    def call(self, callstack, args):
        super().call(callstack, args)
        relation = args[0]
        if not isinstance(relation, Relation):
            raise TypeException(callstack, callstack[-1].location, "empty() argument must be a relation, not {}.".format(args[0].__class__.__name__))
        return self.rel_true if relation.is_empty() else self.rel_false