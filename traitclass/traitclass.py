from abc import ABCMeta
from functools import partial


__all__ = ('IncorrectConfiguration', 'TraitedMeta')


class IncorrectConfiguration(Exception):
    """Raised when TraitedMeta classes are incorrectly defined."""


def extends(cls, trait):
    """
    Takes a class and a trait, returns True iff the class extends the trait.
    """
    try:
        cls_traitcls = cls.__traitclass__
    except AttributeError:
        raise Exception(
            '__traitclass__ not found in {}'.format(cls.__name__))

    return issubclass(cls_traitcls, trait)


class TraitedMeta(ABCMeta):
    """
    Metaclass for a class with traits.

    We first take the __traits__ attribute and convert it into a class and
    attach it as a __traitclass__ attribute on the traited class. Then, we
    take the abstract methods of the __traitclass__ that are not implemented
    on the traited class and attach them as abstract methods on the traited
    class. We then forward __getattr__ lookups of the traited class to its
    __traitclass__ to emulate the lifting/flattening of trait methods/attrs.

    __extends__ is a convenience method to check if a class extends/includes
    a particular trait.
    """

    def __new__(mcs, name, bases, attrs):
        cls = super(TraitedMeta, mcs).__new__(mcs, name, bases, attrs)

        try:
            traits = getattr(cls, '__traits__')
        except AttributeError:
            error = 'Instances of metaclass {} expects a __traits__ defined!'
            raise IncorrectConfiguration(error.format(mcs.__class__.__name__))

        trait_cls = ABCMeta(name + 'Trait', traits, {})
        cls.__traitclass__ = trait_cls

        # lift abstract methods if they are defined on __traitclass__
        if (hasattr(trait_cls, '__abstractmethods__') and
            len(trait_cls.__abstractmethods__) > 0):

            abstracts = set(getattr(trait_cls, '__abstractmethods__', []))

            # pop the non-abstract implementations of the actual class
            # from the lifted abstracts
            cls_dict = {key
                        for key, val in cls.__dict__.items()
                        if not getattr(val, '__isabstractmethod__', False)}
            abstracts.difference_update(cls_dict)
            abstracts.union(trait_cls.__abstractmethods__)

            cls.__abstractmethods__ = frozenset(abstracts)

        old_getattr = getattr(cls, '__getattr__', None)

        def getattr_from_trait_cls(obj, attr):
            """
            Takes an object, an attribute and the object's __getattr__.
            We first looks up the attribute on the object, if the attribute is
            not found on the object, looks up the attribute on the object's
            __traitclass__.
            """
            cls_name = obj.__class__.__name__

            if old_getattr:
                try:
                    return old_getattr(obj, attr)
                except AttributeError:
                    pass

            if attr.startswith('__'):
                raise AttributeError(
                    '{} not defined on {}'.format(attr, cls_name))

            try:
                getattr(obj, '__traitclass__')
            except AttributeError:
                error = '{} does not have a __traitclass__ defined!'
                raise Exception(error.format(cls_name))

            result = getattr(obj.__traitclass__, attr)
            if callable(result):
                return partial(result, obj)
            else:
                return result

        cls.__getattr__ = getattr_from_trait_cls

        cls.__extends__ = classmethod(extends)

        return cls
