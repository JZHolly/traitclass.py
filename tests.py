from unittest import TestCase

from traitclass.traitclass import TraitedMeta, IncorrectConfiguration


class SimpleDescriptor(object):
    def __init__(self, val=None):
        self.val = val

    def __get__(self, obj, objtype):
        return self.val

    def __set__(self, obj, val):
        self.val = val


class SimpleTrait(object):
    __privateattr__ = 1
    descriptor = SimpleDescriptor(10)

    @property
    def is_simple(self):
        return True

    def simple_method(self):
        return 'I am simple'

    def method_with_args(self, foo, bar, baz=0):
        return foo + bar + baz


class SimpleTraitedClass(metaclass=TraitedMeta):
    __traits__ = (SimpleTrait, )


class GetAttrClass(metaclass=TraitedMeta):
    __traits__ = tuple()

    def __getattr__(self, attr):
        """No lookup will fail on this class"""
        return True


class TraitedTests(TestCase):
    def test_no_traits_raises_error(self):
        with self.assertRaises(IncorrectConfiguration):
            class NoTraits(metaclass=TraitedMeta):
                pass

        with self.assertRaises(IncorrectConfiguration):
            TraitedMeta('NoTraits', (), {})

    def test_class_not_subclass_of_trait(self):
        obj = SimpleTraitedClass()
        self.assertFalse(issubclass(SimpleTraitedClass, SimpleTrait))

    def test_trait_class_instantiated(self):
        obj = SimpleTraitedClass()
        self.assertTrue(isinstance(obj.__traitclass__, type))

    def test_private_attrs_of_traits_not_forwarded(self):
        obj = SimpleTraitedClass()
        with self.assertRaises(AttributeError):
            getattr(obj.__privateattr__)

    def test_property_of_traits_forwarded(self):
        obj = SimpleTraitedClass()
        self.assertTrue(obj.is_simple)

    def test_method_of_traits_forwarded(self):
        obj = SimpleTraitedClass()

        self.assertEqual(obj.simple_method(), 'I am simple')
        self.assertEqual(obj.method_with_args(1, bar=2), 3)
        self.assertEqual(obj.method_with_args(bar=2, foo=1, baz=3), 6)
        self.assertEqual(obj.method_with_args(1, 2, 3), 6)

    def test_descriptor_of_traits_forwarded(self):
        obj = SimpleTraitedClass()
        self.assertEqual(obj.descriptor, 10)

        obj.descriptor = 50
        self.assertEqual(obj.descriptor, 50)

    def test_overridden_getattr_takes_precedence(self):
        obj = GetAttrClass()

        self.assertTrue(obj.foo)
        self.assertTrue(obj.__undefinedattr__)
