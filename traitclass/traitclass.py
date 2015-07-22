from abc import ABCMeta
from functools import partial


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
    def __new__(mcs, name, bases, attrs):
        cls = super(TraitedMeta, mcs).__new__(mcs, name, bases, attrs)

        try:
            traits = getattr(cls, '__traits__')
        except AttributeError:
            error = 'Instances of metaclass {} expects a __traits__ defined!'
            raise IncorrectConfiguration(error.format(mcs.__class__.__name__))

        trait_cls = ABCMeta(name + 'Trait', traits, {})
        cls.__traitclass__ = trait_cls

        old_getattr = getattr(cls, '__getattr__', None)

        def getattr_from_trait_cls(obj, attr):
            """
            Takes an object, an attribute and the object's __getattr__.
            We first looks up the attribute on the object, if the attribute is not
            found on the object, looks up the attribute on the objects __traitclass__
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
