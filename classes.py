import numpy as np
import sys
import os
import random
import time
import ctypes
# import string
# from stat import S_ISREG , ST_CTIME , ST_MODE
# import backtrader as bt
import ctypes

kernel32 = ctypes.windll.kernel32
kernel32.SetConsoleMode(kernel32.GetStdHandle(-11) , 7)

RESET = '\033[0m'


class first():
    class Decorators:

        @classmethod
        def pre_init(cls , decorated):
            def wrapper(*args , **kwargs):
                print('before anything')
                decorated(*args , **kwargs)

            return wrapper

    ispairs = False
    count = 0

    def __init__(self , num=1):
        first.count += 1
        self.num1 = num
        print('first init')

    def fun(self):
        print(self.num1 , 'from first - ispairs:' , self.ispairs)

    @Decorators.pre_init
    def with_decor(self):
        print('now the function itself')


class sec(first):
    ispairs = True
    params = (('boz' , 2) , ('olagh' , 3))

    def __init__(self , num):
        print('sec init')
        super().__init__(num)
        self.num = num

    def fun(self):
        super().fun()
        print(self.num , 'from sec - ispairs:' , self.ispairs)
        # print(self.dicts['boz'])

    def work(self):
        for i , p in enumerate(self.params):
            print(p)


class third(first):
    ispairs = True

    def __init__(self , num):
        print('third init')
        super().__init__(num)

    def fun(self):
        self.one = 11
        print(self.one)
        print('no fun from first class')

    def with_decor(self):
        super().with_decor()
        print('from third one')


class fourth(first):
    ispairs = True


def ntimes(f):
    def wrapper(start , end):
        t1 = time.time()
        f(start , end)
        t2 = time.time()
        print('time:' , t2 - t1)

    return wrapper


def log(function):
    def wrapper(*args):
        out_text = function(*args)
        with open('log.txt' , 'a') as log_file:
            log_file.write(out_text + '\n')

    return wrapper


class circle:

    def __init__(self , rad):
        self.op = 5
        self.diameter = 2 * rad

    @property
    def radius(self):
        return self.diameter / 2

    @radius.setter
    def radius(self , rad):
        self.diameter = rad * 2


# MetaClass example:
class MetaClass(type):

    @staticmethod
    def wrap(run):
        """Return a wrapped instance method"""

        def outer(self):
            print("PRE" , self.x)
            return_value = run(self)
            print("POST")
            return return_value

        return outer

    def __new__(cls , name , bases , attrs):
        """If the class has a 'run' method, wrap it"""
        if 'run' in attrs:
            attrs['run'] = cls.wrap(attrs['run'])
        return super(MetaClass , cls).__new__(cls , name , bases , attrs)


class MyClass(metaclass=MetaClass):
    """Use MetaClass to make this class"""

    # __metaclass__ = MetaClass

    def run(self): print('RUN')


class child(MyClass):
    def __init__(self):
        self.x = 5

    def run(self):
        pass


if __name__ == '__main__':
    # one = first()
    # two = sec(num=2)
    # two.fun()
    # three = third(num=3)
    # three.with_decor()
    #
    # two.with_decor()

    # **************************************
    # myinstance = MyClass()
    #
    # # Prints PRE RUN POST
    # myinstance.run()
    instance = child()
    instance.run()
